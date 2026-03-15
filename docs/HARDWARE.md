# Hardware Guide - Neighborhood BBS

## Supported Platforms

### Primary Platforms

#### 1. Zima Board
**Status:** ✅ Full Support

- **Specs:** ARMv8 Multi-core, 4GB RAM, up to 128GB Storage
- **OS:** Zima OS (Linux-based)
- **Ideal For:** Primary community server
- **Advantages:**
  - High performance
  - Large storage capacity
  - Full Linux environment
  - Reliable 24/7 operation

**Deployment:** See [firmware/zima/README.md](firmware/zima/README.md)

#### 2. Raspberry Pi
**Status:** ✅ Full Support (NEW!)

- **Specs:** ARM Multi-core, 2-8GB RAM, microSD card
- **Models:** Pi 3B+, Pi 4, Pi 5
- **OS:** Raspberry Pi OS (Linux-based)
- **Ideal For:** Community server, neighborhood hub
- **Advantages:**
  - Affordable ($35-80)
  - Wide community support
  - Easy to set up
  - Great for learning
  - Low power consumption (~5W)

**Deployment:** See [firmware/raspberry-pi/README.md](firmware/raspberry-pi/README.md)

**Quick Start:**
```bash
curl https://raw.githubusercontent.com/Gh0stlyKn1ght/Neighborhood_BBS/main/firmware/raspberry-pi/setup.sh | bash
```

Or with Docker:
```bash
cd docker
docker-compose -f docker-compose.yml up -d
```

#### 3. ESP8266
**Status:** ✅ Supported

- **Specs:** 80/160MHz CPU, 160KB RAM, 4MB Flash
- **OS:** MicroPython
- **Ideal For:** Sensor nodes, lightweight clients
- **Advantages:**
  - Low power consumption
  - Small form factor
  - WiFi built-in
  - Cost-effective

**Deployment:** See [firmware/esp8266/README.md](firmware/esp8266/README.md)

### Planned Support

#### ESP32
**Status:** 🔄 In Progress

- Higher performance than ESP8266
- More storage
- Better for local server node

#### Orange Pi
**Status:** 📋 Planned

- Alternative to Raspberry Pi
- Lower cost
- Good performance

#### Generic x86
**Status:** 📋 Planned

- Desktop/laptop deployment
- VPS hosting
- Docker containers

## Hardware Specifications Comparison

| Feature | Raspberry Pi 4 | Zima Board | ESP8266 | ESP32 |
|---------|---|-----------|--------|-------|
| Processor | ARM Quad-core 1.5GHz | ARMv8 Multi-core | Xtensa 80/160MHz | Xtensa Dual-core |
| RAM | 2-8GB | 4GB+ | 160KB | 520KB |
| Storage | microSD (32GB+) | 128GB+ | 4MB | 16MB+ |
| WiFi | Yes | Yes | Yes | Yes |
| Ethernet | Yes (USB) | Yes | No | No |
| Power | ~5W | ~12W | <100mA | 50-100mA |
| OS | Linux | Linux | MicroPython | MicroPython |
| Cost | $$$ | $$$$ | $ | $$ |
| Setup Time | 30 min | 30 min | 1-2 hours | 1-2 hours |
| Community | Very Large | Small | Large | Large |
| Deployment | Server/Hub | Server | Client/Sensor | Gateway |
| OS | Linux | MicroPython | MicroPython |
| Cost | $$$$ | $ | $$ |
| Deployment | Server | Client/Sensor | Node/Gateway |

## Connectivity Options

### WiFi
- **Best for:** All platforms
- **Speed:** Adequate for typical usage
- **Range:** 30-100 meters

### Ethernet
- **Best for:** Zima Board (primary server)
- **Speed:** Recommended for stable connections
- **Reliability:** Highest

### Mesh Networks
- **Best for:** ESP8266/ESP32 deployments
- **Benefits:** Self-healing, extended range
- **Protocol:** ThingMesh or similar

## Power Considerations

### Zima Board
- Requires stable 12V power supply
- UPS recommended for reliability
- ~12W typical consumption

### ESP8266
- Can run on battery (AA batteries)
- Sleep modes for power efficiency
- ~80-100mA active operation

### Solar Power Options
For remote neighborhood nodes:
- Small solar panel (5-10W)
- Battery backup (2000-5000mAh)
- MPPT charge controller
- Suitable for ESP8266/ESP32

## Network Architecture Examples

### Network Topology 1: Central + Satellites
```
          ┌─────────────────┐
          │   Zima Board    │
          │   (Main Server) │
          └────────┬────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
    ┌───▼──┐  ┌───▼──┐  ┌───▼──┐
    │ ESP  │  │ ESP  │  │ ESP  │
    │ 8266 │  │ 8266 │  │ 8266 │
    └──────┘  └──────┘  └──────┘
   (Nodes)  (Sensors) (Gateways)
```

### Network Topology 2: Mesh Network
```
    ESP-1 ─── ESP-2
      │  ╲    /  │
      │   ╲  /   │
      │    ╱╲    │
      │   /  ╲   │
    ESP-3 ─── ESP-4
      │
      └──────┬──────┐
             │      │
          Zima   (Internet)
```

## Installation Guide by Device

### Quick Links
- [Zima Board Setup](firmware/zima/README.md)
- [ESP8266 Setup](firmware/esp8266/README.md)
- [General Setup Guide](docs/SETUP.md)

## Troubleshooting by Platform

### Zima Board
- See: `firmware/zima/README.md`

### ESP8266
- See: `firmware/esp8266/README.md`

## Resources

- [Zima Board Official](https://www.cardberry.cc/zima)
- [MicroPython Documentation](https://docs.micropython.org/)
- [ESP8266 Community](https://github.com/esp8266/Arduino)
- [Arduino IDE](https://www.arduino.cc/en/software)

## Future Hardware Support

We're always looking to expand platform support:
- Orange Pi
- Beaglebone Black
- Arduino-based systems
- OpenWrt routers

Interested in adding support for a device? 
[Create an issue](https://github.com/yourusername/Neighborhood_BBS/issues)!

---

For deployment instructions, see the [Setup Guide](docs/SETUP.md).
