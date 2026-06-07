# ⛓️ ChainClaim — Enterprise Blockchain Insurance Platform
> Polygon zkEVM + Chainlink Oracle + IPFS + IoT Sensors

---

## 📸 Screenshots

![Dashboard](assets/screenshots/dashboard.png)

![IoT Analytics](assets/screenshots/iot-analytics.png)

![New Claim](assets/screenshots/new-claim.png)

---

## 🏗️ Project Structure

```
CHAINCLAIM/
├── backend/
│   ├── controllers/
│   │   └── claimController.js      # Claim CRUD logic
│   ├── models/
│   │   ├── Claim.js                # Claim schema
│   │   └── User.js                 # User schema
│   └── routes/
│       └── claimRoutes.js          # API routes
│   └── server.js                   # Express server
├── contracts/
│   └── ClaimProcessor.sol          # Solidity smart contract
├── scripts/
│   └── deploy.js                   # Hardhat deploy script
├── iot/
│   └── sensor_collector.py         # IoT sensor data
├── deployments/                    # Auto-generated after deploy
├── assets/screenshots/             # Project screenshots
├── index.html                      # Frontend
├── script.js                       # Frontend JS
├── style.css                       # Frontend CSS
├── hardhat.config.js               # Hardhat config
├── .env                            # Environment vars
├── .env.example                    # Env template
└── package.json                    # Dependencies
```

---

## 🚀 Setup & Run

### 1. Install dependencies
```bash
npm install
```

### 2. Setup environment
```bash
cp .env.example .env
# Edit .env with your actual keys
```

### 3. Compile smart contracts
```bash
npm run compile
```

### 4. Deploy to testnet
```bash
npm run deploy:testnet
```

### 5. Start backend server
```bash
npm run dev
```

### 6. Start IoT collector
```bash
npm run iot
```

---

## 🌐 Network Info

| Network | Chain ID | RPC |
|---------|----------|-----|
| Polygon zkEVM Testnet | 1442 | https://rpc.public.zkevm-test.net |
| Polygon zkEVM Mainnet | 1101 | https://zkevm-rpc.com |

---

## 📡 API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/claims` | All claims |
| POST | `/api/claims` | New claim |
| GET | `/api/claims/:id` | Single claim |
| PUT | `/api/claims/:id` | Update claim |
| DELETE | `/api/claims/:id` | Delete claim |
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/register` | User register |

---

## 🔑 .env Keys Required

```
MONGO_URI            → MongoDB connection string
JWT_SECRET           → Auth secret key
PRIVATE_KEY          → Wallet private key (for deployment)
POLYGON_ZKEVM_RPC    → RPC endpoint
POLYGONSCAN_API_KEY  → For contract verification
INFURA_IPFS_PROJECT_ID → IPFS storage
```

---

## ⚡ Tech Stack

- **Blockchain**: Polygon zkEVM
- **Smart Contracts**: Solidity 0.8.19 + Hardhat
- **Oracle**: Chainlink v2.1
- **Storage**: IPFS (Infura)
- **Backend**: Node.js + Express + MongoDB
- **IoT**: Python sensor collector
- **Frontend**: Vanilla JS + Web3.js

---

## 👨‍💻 Developer

**Kaveesh Dhiman**

- 🏢 Ex-Intern @ National Informatics Centre (NIC), Government of India
- 🎓 B.Tech CSE — Dronacharya College of Engineering
- 📧 [kaveesh9876@gmail.com](mailto:kaveesh9876@gmail.com)
