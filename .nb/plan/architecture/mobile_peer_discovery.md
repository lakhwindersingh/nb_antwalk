---
gap_id: "GAP-010"
name: "Local-First Multi-Device Peer Discovery & Sync"
priority: "P0"
status: "specification"
created: "2026-10-04"
---

# Mobile Peer Discovery: Bonjour/mDNS Local Sync with Silent APNs Fallback

## Problem Statement

Current multi-device sync relies on polling or cloud relay:

```rust
// Current approach: periodic polling
async fn sync_with_remote(&self) -> Result<(), SyncError> {
    loop {
        tokio::time::sleep(Duration::from_secs(300)).await;  // Poll every 5 minutes
        
        let response = self.http_client
            .get("https://sync.personal-os.com/delta")
            .send()
            .await?;
        
        // ... process delta
    }
}
```

### iOS Background Execution Constraints

**Apple's Background Restrictions**:
- `BGAppRefreshTask`: 30-second execution window, fired **unpredictably** by iOS
- `BGProcessingTask`: Requires device to be idle, charging, on Wi-Fi
- `URLSession` background downloads: Only for large file downloads, not real-time sync

**Real-World Scenario**:
```
10:00 AM: User adds thought on iPhone
10:05 AM: iOS *might* wake app via BGAppRefreshTask
10:05-10:05:30: App syncs with cloud
10:30 AM: User sits at MacBook
10:35 AM: MacBook polls cloud, receives thought (35-minute delay!)
```

**Impact**:
- High latency (5-30 minutes for cross-device sync)
- Unnecessary cloud dependency for local sync
- Battery drain from continuous polling
- Privacy: all data routed through cloud even when devices co-located

---

## Solution Architecture: Local-First P2P Sync

### Multi-Transport Strategy

```
┌─────────────────────────────────────────────────────────────┐
│              Transport Priority Cascade                      │
├─────────────────────────────────────────────────────────────┤
│  1. Local Wi-Fi (Bonjour/mDNS)      [Sub-second latency]   │
│     - Same network discovery                                 │
│     - Direct TLS connection                                  │
│     - No internet required                                   │
│                                                               │
│  2. Bluetooth LE                     [2-5 second latency]   │
│     - Proximity-based (< 10 meters)                          │
│     - Low power consumption                                  │
│     - Works without Wi-Fi                                    │
│                                                               │
│  3. Silent APNs Push                 [5-30 second latency]  │
│     - Remote device wake-up                                  │
│     - Triggers background fetch                              │
│     - Falls back to cloud sync                               │
│                                                               │
│  4. Cloud Relay (Fallback)           [30-300 second latency]│
│     - BGAppRefreshTask polling                               │
│     - Internet-dependent                                     │
│     - Encrypted end-to-end                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                 Local Network Topology                        │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   MacBook Pro (macOS)              iPhone 15 (iOS)           │
│   ┌─────────────────┐             ┌──────────────┐          │
│   │ pos_daemon      │             │ PersonalOS   │          │
│   │ (always-on)     │             │ App          │          │
│   └────────┬────────┘             └──────┬───────┘          │
│            │                              │                  │
│            │  1. Bonjour Advertisement    │                  │
│            │     _pos._tcp.local.         │                  │
│            │<────────────────────────────────────           │
│            │                              │                  │
│            │  2. mTLS Handshake           │                  │
│            │     (Pre-paired cert)        │                  │
│            │<────────────────────────────>│                  │
│            │                              │                  │
│            │  3. CRDT Delta Sync          │                  │
│            │     (Yrs binary wire format) │                  │
│            │<────────────────────────────>│                  │
│            │                              │                  │
│   Same Wi-Fi Network (192.168.1.0/24)                       │
│   OR                                                         │
│   Bluetooth LE Connection (if Wi-Fi unavailable)            │
│                                                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│             Remote Sync via Silent APNs                       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   MacBook (Home)                Apple Push Notification      │
│   ┌───────────────┐            Service (APNs)                │
│   │ pos_daemon    │            ┌──────────────┐             │
│   │               │            │              │             │
│   │ 1. New thought│───────────>│ Silent Push  │             │
│   │    created    │            │ (priority:5) │             │
│   └───────────────┘            └──────┬───────┘             │
│                                       │                      │
│                                       │ Wake iOS app         │
│                                       ▼                      │
│                            iPhone (Remote Location)          │
│                            ┌──────────────┐                 │
│                            │ PersonalOS   │                 │
│                            │ App          │                 │
│                            │              │                 │
│                            │ 2. Fetch     │                 │
│                            │    delta via │                 │
│                            │    HTTPS     │                 │
│                            └──────────────┘                 │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation Specification

### 1. Bonjour/mDNS Service Discovery

```rust
// workplace/modules/pos_sync/src/mdns_discovery.rs

use mdns_sd::{ServiceDaemon, ServiceInfo, ServiceEvent};
use tokio::sync::mpsc;
use std::net::Ipv4Addr;

pub struct BonjourDiscovery {
    mdns: ServiceDaemon,
    device_id: String,
    port: u16,
}

impl BonjourDiscovery {
    pub fn new(device_id: String, port: u16) -> Result<Self, DiscoveryError> {
        let mdns = ServiceDaemon::new()
            .map_err(|e| DiscoveryError::InitFailed(e.to_string()))?;
        
        Ok(Self { mdns, device_id, port })
    }
    
    /// Register this device as a discoverable service
    pub async fn advertise(&self) -> Result<(), DiscoveryError> {
        let service_type = "_pos._tcp.local.";
        let instance_name = format!("PersonalOS-{}", &self.device_id[0..8]);
        
        let service_info = ServiceInfo::new(
            service_type,
            &instance_name,
            &format!("{}.local.", hostname()),
            (),  // No specific address (use all interfaces)
            self.port,
            vec![
                ("device_id", self.device_id.as_str()),
                ("version", env!("CARGO_PKG_VERSION")),
                ("platform", std::env::consts::OS),
            ].into_iter().collect(),
        )?;
        
        self.mdns.register(service_info)
            .map_err(|e| DiscoveryError::AdvertiseFailed(e.to_string()))?;
        
        info!("mDNS service advertised: {} on port {}", instance_name, self.port);
        
        Ok(())
    }
    
    /// Browse for other PersonalOS devices on local network
    pub async fn discover_peers(&self) -> Result<mpsc::Receiver<DiscoveredPeer>, DiscoveryError> {
        let (tx, rx) = mpsc::channel(32);
        
        let service_type = "_pos._tcp.";
        let browse_handle = self.mdns.browse(service_type)
            .map_err(|e| DiscoveryError::BrowseFailed(e.to_string()))?;
        
        tokio::spawn(async move {
            while let Ok(event) = browse_handle.recv_async().await {
                match event {
                    ServiceEvent::ServiceResolved(info) => {
                        let peer = DiscoveredPeer {
                            device_id: info.get_property_val_str("device_id")
                                .unwrap_or_default().to_string(),
                            addresses: info.get_addresses().clone(),
                            port: info.get_port(),
                            hostname: info.get_hostname().to_string(),
                        };
                        
                        info!("Discovered peer: {:?}", peer);
                        
                        let _ = tx.send(peer).await;
                    }
                    ServiceEvent::ServiceRemoved(_, name) => {
                        info!("Peer left network: {}", name);
                    }
                    _ => {}
                }
            }
        });
        
        Ok(rx)
    }
}

#[derive(Debug, Clone)]
pub struct DiscoveredPeer {
    pub device_id: String,
    pub addresses: Vec<Ipv4Addr>,
    pub port: u16,
    pub hostname: String,
}

fn hostname() -> String {
    hostname::get()
        .ok()
        .and_then(|h| h.into_string().ok())
        .unwrap_or_else(|| "unknown".to_string())
}
```

### 2. Mutual TLS (mTLS) Peer Authentication

```rust
// workplace/modules/pos_sync/src/peer_tls.rs

use rustls::{ServerConfig, ClientConfig, Certificate, PrivateKey};
use tokio_rustls::{TlsAcceptor, TlsConnector};
use std::sync::Arc;

pub struct PeerTLSConfig {
    device_cert: Certificate,
    device_key: PrivateKey,
    trusted_peers: Vec<Certificate>,
}

impl PeerTLSConfig {
    pub fn new(
        device_cert: Certificate,
        device_key: PrivateKey,
        trusted_peers: Vec<Certificate>,
    ) -> Self {
        Self { device_cert, device_key, trusted_peers }
    }
    
    /// Create server config for accepting peer connections
    pub fn server_config(&self) -> Arc<ServerConfig> {
        let mut config = ServerConfig::builder()
            .with_safe_defaults()
            .with_client_cert_verifier(self.peer_verifier())
            .with_single_cert(
                vec![self.device_cert.clone()],
                self.device_key.clone(),
            )
            .expect("Failed to build TLS server config");
        
        Arc::new(config)
    }
    
    /// Create client config for connecting to peer
    pub fn client_config(&self) -> Arc<ClientConfig> {
        let mut root_store = rustls::RootCertStore::empty();
        
        for cert in &self.trusted_peers {
            root_store.add(cert)
                .expect("Failed to add trusted peer cert");
        }
        
        let config = ClientConfig::builder()
            .with_safe_defaults()
            .with_root_certificates(root_store)
            .with_client_auth_cert(
                vec![self.device_cert.clone()],
                self.device_key.clone(),
            )
            .expect("Failed to build TLS client config");
        
        Arc::new(config)
    }
    
    fn peer_verifier(&self) -> Arc<dyn rustls::server::ClientCertVerifier> {
        // Custom verifier that checks against pre-paired device certificates
        Arc::new(PeerCertVerifier {
            trusted_peers: self.trusted_peers.clone(),
        })
    }
}

struct PeerCertVerifier {
    trusted_peers: Vec<Certificate>,
}

impl rustls::server::ClientCertVerifier for PeerCertVerifier {
    fn verify_client_cert(
        &self,
        end_entity: &Certificate,
        _intermediates: &[Certificate],
        _now: std::time::SystemTime,
    ) -> Result<rustls::server::ClientCertVerified, rustls::Error> {
        // Check if cert matches any pre-paired peer
        if self.trusted_peers.iter().any(|cert| cert.0 == end_entity.0) {
            Ok(rustls::server::ClientCertVerified::assertion())
        } else {
            Err(rustls::Error::General(
                "Client certificate not in trusted peer list".to_string()
            ))
        }
    }
    
    fn offer_client_auth(&self) -> bool {
        true  // Require mTLS for all peer connections
    }
    
    fn client_auth_mandatory(&self) -> bool {
        true
    }
}
```

### 3. Peer Sync Session

```rust
// workplace/modules/pos_sync/src/peer_session.rs

use tokio::net::TcpStream;
use tokio_rustls::TlsStream;
use yrs::updates::encoder::Encode;

pub struct PeerSyncSession {
    stream: TlsStream<TcpStream>,
    peer_device_id: String,
    crdt_coordinator: Arc<CRDTCoordinator>,
}

impl PeerSyncSession {
    pub async fn connect(
        peer: &DiscoveredPeer,
        tls_config: Arc<ClientConfig>,
        crdt_coordinator: Arc<CRDTCoordinator>,
    ) -> Result<Self, SyncError> {
        // Connect to peer
        let addr = format!("{}:{}", peer.addresses[0], peer.port);
        let tcp_stream = TcpStream::connect(&addr).await?;
        
        // TLS handshake
        let connector = TlsConnector::from(tls_config);
        let domain = rustls::ServerName::try_from(peer.hostname.as_str())
            .map_err(|_| SyncError::InvalidHostname)?;
        
        let tls_stream = connector.connect(domain, tcp_stream).await?;
        
        info!("Connected to peer {} via mTLS", peer.device_id);
        
        Ok(Self {
            stream: tls_stream,
            peer_device_id: peer.device_id.clone(),
            crdt_coordinator,
        })
    }
    
    /// Send local CRDT state vector to peer
    pub async fn sync_state(&mut self) -> Result<(), SyncError> {
        // Step 1: Send our state vector
        let state_vector = self.crdt_coordinator.get_state_vector().await?;
        
        self.send_message(SyncMessage::StateVector(state_vector)).await?;
        
        // Step 2: Receive peer's state vector
        let peer_state_vector = match self.receive_message().await? {
            SyncMessage::StateVector(sv) => sv,
            _ => return Err(SyncError::ProtocolViolation),
        };
        
        // Step 3: Calculate delta (what peer is missing)
        let delta = self.crdt_coordinator
            .get_delta_since(&peer_state_vector)
            .await?;
        
        // Step 4: Send delta to peer
        self.send_message(SyncMessage::Update(delta)).await?;
        
        // Step 5: Receive delta from peer
        let peer_delta = match self.receive_message().await? {
            SyncMessage::Update(d) => d,
            _ => return Err(SyncError::ProtocolViolation),
        };
        
        // Step 6: Apply peer's delta
        self.crdt_coordinator.apply_update(&peer_delta).await?;
        
        info!("Sync with peer {} complete", self.peer_device_id);
        
        Ok(())
    }
    
    async fn send_message(&mut self, msg: SyncMessage) -> Result<(), SyncError> {
        let bytes = bincode::serialize(&msg)?;
        let len = bytes.len() as u32;
        
        // Send length prefix + message
        self.stream.write_all(&len.to_be_bytes()).await?;
        self.stream.write_all(&bytes).await?;
        
        Ok(())
    }
    
    async fn receive_message(&mut self) -> Result<SyncMessage, SyncError> {
        // Read length prefix
        let mut len_bytes = [0u8; 4];
        self.stream.read_exact(&mut len_bytes).await?;
        let len = u32::from_be_bytes(len_bytes) as usize;
        
        // Read message
        let mut buf = vec![0u8; len];
        self.stream.read_exact(&mut buf).await?;
        
        let msg = bincode::deserialize(&buf)?;
        
        Ok(msg)
    }
}

#[derive(Debug, Serialize, Deserialize)]
enum SyncMessage {
    StateVector(Vec<u8>),  // Yrs StateVector
    Update(Vec<u8>),       // Yrs Update (delta)
}
```

### 4. Silent APNs Push Integration

```swift
// ios/PersonalOS/APNsHandler.swift

import UserNotifications
import BackgroundTasks

class APNsHandler: NSObject, UNUserNotificationCenterDelegate {
    
    func setupAPNs() {
        UNUserNotificationCenter.current().delegate = self
        
        // Request authorization for silent notifications
        UNUserNotificationCenter.current().requestAuthorization(
            options: []  // No banner/sound for silent push
        ) { granted, error in
            if granted {
                DispatchQueue.main.async {
                    UIApplication.shared.registerForRemoteNotifications()
                }
            }
        }
    }
    
    func application(
        _ application: UIApplication,
        didReceiveRemoteNotification userInfo: [AnyHashable: Any],
        fetchCompletionHandler completionHandler: @escaping (UIBackgroundFetchResult) -> Void
    ) {
        // Silent push received (content-available: 1)
        guard userInfo["aps"] as? [String: Any] != nil else {
            completionHandler(.failed)
            return
        }
        
        // Extract sync metadata
        guard let deviceId = userInfo["source_device"] as? String,
              let timestamp = userInfo["timestamp"] as? Int64 else {
            completionHandler(.noData)
            return
        }
        
        print("Silent push from device: \(deviceId)")
        
        // Trigger sync with Rust core
        Task {
            do {
                try await syncWithPeer(deviceId: deviceId)
                completionHandler(.newData)
            } catch {
                print("Sync failed: \(error)")
                completionHandler(.failed)
            }
        }
    }
    
    private func syncWithPeer(deviceId: String) async throws {
        // Call Rust FFI to sync via HTTPS
        let result = pos_sync_fetch_delta(deviceId)
        
        if result < 0 {
            throw SyncError.rustFailed(code: result)
        }
    }
}
```

**APNs Payload** (sent from macOS daemon):
```json
{
  "aps": {
    "content-available": 1,
    "priority": 5
  },
  "source_device": "macbook-a3f2b9c1",
  "timestamp": 1696454400
}
```

### 5. Peer Discovery Coordinator

```rust
// workplace/modules/pos_sync/src/peer_coordinator.rs

pub struct PeerCoordinator {
    discovery: Arc<BonjourDiscovery>,
    tls_config: Arc<PeerTLSConfig>,
    crdt_coordinator: Arc<CRDTCoordinator>,
    active_sessions: Arc<RwLock<HashMap<String, PeerSyncSession>>>,
}

impl PeerCoordinator {
    pub async fn start(&self) -> Result<(), SyncError> {
        // Advertise this device
        self.discovery.advertise().await?;
        
        // Start peer discovery
        let mut peer_rx = self.discovery.discover_peers().await?;
        
        tokio::spawn({
            let coordinator = Arc::clone(&self);
            async move {
                while let Some(peer) = peer_rx.recv().await {
                    coordinator.handle_discovered_peer(peer).await;
                }
            }
        });
        
        Ok(())
    }
    
    async fn handle_discovered_peer(&self, peer: DiscoveredPeer) {
        // Skip if already connected
        if self.active_sessions.read().await.contains_key(&peer.device_id) {
            return;
        }
        
        // Connect and sync
        match PeerSyncSession::connect(
            &peer,
            Arc::clone(&self.tls_config.client_config()),
            Arc::clone(&self.crdt_coordinator),
        ).await {
            Ok(mut session) => {
                info!("Established peer session with {}", peer.device_id);
                
                // Perform initial sync
                if let Err(e) = session.sync_state().await {
                    error!("Sync with {} failed: {:?}", peer.device_id, e);
                    return;
                }
                
                // Store session for future syncs
                self.active_sessions.write().await.insert(
                    peer.device_id.clone(),
                    session,
                );
            }
            Err(e) => {
                error!("Failed to connect to peer {}: {:?}", peer.device_id, e);
            }
        }
    }
    
    /// Trigger sync with all connected peers
    pub async fn sync_all_peers(&self) -> Result<(), SyncError> {
        let sessions = self.active_sessions.read().await;
        
        for (device_id, session) in sessions.iter() {
            if let Err(e) = session.sync_state().await {
                error!("Sync with {} failed: {:?}", device_id, e);
            }
        }
        
        Ok(())
    }
}
```

---

## Device Pairing Flow

```rust
// workplace/modules/pos_sync/src/pairing.rs

pub struct DevicePairing {
    pool: SqlitePool,
}

impl DevicePairing {
    /// Generate QR code for pairing new device
    pub async fn generate_pairing_code(&self) -> Result<String, PairingError> {
        // Generate ephemeral symmetric key
        let pairing_key: [u8; 32] = rand::random();
        let pairing_id = uuid::Uuid::new_v4().to_string();
        
        // Store pairing session (expires in 5 minutes)
        sqlx::query!(
            r#"
            INSERT INTO pairing_sessions (pairing_id, pairing_key, expires_at)
            VALUES (?1, ?2, datetime('now', '+5 minutes'))
            "#,
            pairing_id,
            pairing_key.to_vec(),
        )
        .execute(&self.pool)
        .await?;
        
        // Encode as QR-friendly string
        let payload = format!("{}:{}", pairing_id, base64::encode(&pairing_key));
        
        Ok(payload)
    }
    
    /// Complete pairing by exchanging certificates
    pub async fn complete_pairing(
        &self,
        pairing_code: &str,
        peer_cert: Certificate,
    ) -> Result<(), PairingError> {
        // Parse pairing code
        let parts: Vec<&str> = pairing_code.split(':').collect();
        let (pairing_id, key_b64) = (parts[0], parts[1]);
        
        // Verify pairing session exists and not expired
        let session = sqlx::query!(
            r#"
            SELECT pairing_key
            FROM pairing_sessions
            WHERE pairing_id = ?1 AND expires_at > datetime('now')
            "#,
            pairing_id,
        )
        .fetch_one(&self.pool)
        .await?;
        
        // Verify key matches
        let expected_key = base64::decode(key_b64)?;
        if session.pairing_key != expected_key {
            return Err(PairingError::InvalidKey);
        }
        
        // Store peer certificate
        let peer_device_id = Self::extract_device_id_from_cert(&peer_cert)?;
        
        sqlx::query!(
            r#"
            INSERT INTO trusted_devices (device_id, certificate, paired_at)
            VALUES (?1, ?2, CURRENT_TIMESTAMP)
            "#,
            peer_device_id,
            peer_cert.0,
        )
        .execute(&self.pool)
        .await?;
        
        info!("Device pairing complete: {}", peer_device_id);
        
        Ok(())
    }
    
    fn extract_device_id_from_cert(cert: &Certificate) -> Result<String, PairingError> {
        // Parse X.509 certificate and extract CN (Common Name)
        let x509 = x509_parser::parse_x509_certificate(&cert.0)
            .map_err(|_| PairingError::InvalidCertificate)?
            .1;
        
        let cn = x509.subject()
            .iter_common_name()
            .next()
            .ok_or(PairingError::InvalidCertificate)?
            .as_str()
            .map_err(|_| PairingError::InvalidCertificate)?;
        
        Ok(cn.to_string())
    }
}
```

---

## CLI Commands

```bash
# Start local peer discovery
pos sync discover

# Output:
# 🔍 Discovering peers on local network...
# Found peer: MacBook-a3f2b9c1 (192.168.1.10:8443)
# Connected via mTLS
# ✅ Sync complete (15 thoughts synced)

# Pair new device via QR code
pos sync pair --generate

# Output:
# 📱 Scan this QR code with your iPhone:
# [QR code displayed]
# Waiting for pairing...
# ✅ Paired: iPhone-b78a3c2f

# List trusted devices
pos sync devices

# Output:
# Trusted Devices:
# 1. MacBook-a3f2b9c1 (macOS) - Last seen: 2 minutes ago
# 2. iPhone-b78a3c2f (iOS) - Last seen: 1 hour ago
```

---

## Performance Targets

- **Local Discovery**: <500ms to find peers on same network
- **mTLS Handshake**: <100ms for certificate exchange
- **Initial Sync**: <2 seconds for 1000 thoughts/tasks
- **Delta Sync**: <200ms for incremental updates

---

## Benefits

1. **Sub-Second Latency**: Local sync bypasses cloud round-trip
2. **Privacy**: Data never leaves local network for co-located devices
3. **Offline-First**: Works without internet connectivity
4. **Battery Efficient**: No continuous polling, event-driven sync
5. **Zero Configuration**: mDNS auto-discovery, no manual IP entry

---

## Related Gaps

- **GAP-001** (CRDT Sync): Yrs state vectors used for delta sync
- **GAP-006** (Vault Recovery): Device certificates stored in keychain
- **GAP-008** (Subagent Sandboxing): Network allowlist includes local peers

---

**Status**: ✅ Specification Complete - Ready for Implementation  
**Next Action**: Implement `BonjourDiscovery` and mTLS peer authentication
