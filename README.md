# 👕 AK E-Commerce Clothing

> A modern, responsive clothing e-commerce platform with an integrated **Virtual Fitting Room** powered by **Python, OpenCV, and MediaPipe**.

AK E-Commerce Clothing is a full-stack fashion e-commerce project designed to provide customers with a modern online shopping experience while experimenting with **computer vision-based virtual clothing try-on technology**.

The platform combines a responsive frontend with a Python/Flask backend and computer vision technologies to allow users to preview selected clothing items through their camera.

---

## ✨ Features

### 🛍️ E-Commerce

* Modern fashion-focused UI
* Responsive design for desktop, tablet, and mobile
* Product browsing
* Product detail pages
* Category filtering
* Product search
* New arrivals
* Shopping cart
* Wishlist
* Product size assistant interface

### 👗 Virtual Fitting Room

* Real-time camera access
* Human pose detection
* Body landmark detection
* Virtual clothing overlay
* Upper-body clothing fitting
* Lower-body clothing fitting
* Garment positioning based on body landmarks
* Real-time preview
* Camera start/stop controls
* Clothing selection through the product page

### 🎨 UI / UX

* Clean modern fashion-store design
* Responsive navigation
* Product cards
* Product image galleries
* Modal-based Virtual Fitting Room
* Toast notifications
* Shopping cart drawer
* Search modal
* Mobile navigation menu

### Screenshots
![alt text](Screenshots/Screenshot%202026-10-01%20001734.png)
![alt text](Screenshots/Screenshot%202026-10-01%20001734.png)
![alt text](Screenshots/Screenshot%202026-10-01%20001803.png)
![alt text](Screenshots/Screenshot%202026-10-01%20001812.png)

---

# 🧠 Virtual Fitting Room

One of the main features of this project is the **Virtual Fitting Room**.

The system uses computer vision to detect the user's body position and place a selected garment over the detected body region.

### Technology Pipeline

```text
User Camera
     │
     ▼
OpenCV
     │
     ▼
Video Frame Processing
     │
     ▼
MediaPipe Pose Detection
     │
     ▼
Body Landmarks
     │
     ▼
Garment Position Calculation
     │
     ▼
Clothing Overlay
     │
     ▼
Real-Time Virtual Try-On
```

The system is designed to process the camera feed in real time while maintaining a responsive experience.

---

# 🛠️ Technologies

## Frontend

* HTML5
* CSS3
* JavaScript
* Responsive Web Design
* Google Fonts

## Backend

* Python
* Flask
* REST API

## Computer Vision

* OpenCV
* MediaPipe
* MediaPipe Pose Landmarker

## Development Tools

* Git
* GitHub
* Visual Studio Code
* Python Virtual Environment

---
```

---

# 🚀 Getting Started

## 1. Clone the repository

```bash
git clone https://github.com/TechAkii/AK-E-Commerce-Clothing.git

Move into the project directory:

```bash
cd AK-E-Commerce-Clothing

## 2. Create a Python virtual environment

Windows:

```bash
python -m venv venv


Activate it:

### PowerShell

```powershell
venv\Scripts\Activate.ps1


### Command Prompt

```cmd
venv\Scripts\activate


---

## 3. Install dependencies

```bash
pip install -r requirements.txt


---

## 4. Start the Flask backend

```bash
python app.py


The backend will run locally, typically at:

```text
http://127.0.0.1:5000


---

## 5. Open the website

Open the frontend using a local development server such as **VS Code Live Server**.

Then:

```text
Home
  ↓
Shop
  ↓
Select a Product
  ↓
Try It Virtually
  ↓
Open Camera
  ↓
Virtual Fitting Room
```

---

# 📸 Virtual Try-On Usage

1. Open the **Shop** page.
2. Select a clothing product.
3. Open the product details.
4. Click **Try It Virtually**.
5. Allow camera access.
6. Click **Open Camera**.
7. Stand in front of the camera.
8. The system detects your body landmarks.
9. The selected garment is positioned over your body.
10. Use the fitting-room controls to preview the clothing.

---

# ⚙️ Configuration

The Virtual Try-On backend currently runs locally.

The frontend communicates with the Flask backend through the configured Virtual Try-On API endpoint.

For local development, the API can use:

```text
http://127.0.0.1:5000
```

When deploying the project, this should be changed to the production backend URL.

---

# 🧪 Current Development Status

### Completed

* [x] Responsive clothing store UI
* [x] Product listing
* [x] Product detail page
* [x] Product categories
* [x] Search interface
* [x] Shopping cart
* [x] Wishlist
* [x] Virtual Fitting Room interface
* [x] Camera integration
* [x] OpenCV integration
* [x] MediaPipe pose detection
* [x] Clothing overlay
* [x] Real-time fitting-room preview
* [x] GitHub repository

### Planned

* [ ] MySQL database
* [ ] User registration and authentication
* [ ] Secure login system
* [ ] Admin dashboard
* [ ] Product management
* [ ] Inventory management
* [ ] Order management
* [ ] Payment integration
* [ ] Secure image upload
* [ ] Improved garment fitting
* [ ] Improved body-size estimation
* [ ] Production deployment
* [ ] Cloud-based Virtual Try-On API

---

# 🗄️ Future Database Architecture

The current version uses static product data.

Database integration is planned for a future version.

The planned architecture is:

```text
                    ┌──────────────┐
                    │   Frontend   │
                    │ HTML/CSS/JS  │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Flask REST   │
                    │     API      │
                    └──────┬───────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       ┌──────────────┐        ┌────────────────┐
       │    MySQL     │        │ Virtual Try-On │
       │   Database   │        │ OpenCV/MediaPipe│
       └──────────────┘        └────────────────┘
```

Planned database entities include:

```text
Users
Products
Categories
Orders
Order Items
Cart
Wishlist
```


# 📋 Requirements

Recommended environment:

```text
Python 3.x
Modern web browser
Webcam
Git
VS Code
```

A webcam is required for the Virtual Fitting Room.

---

# 🧑‍💻 Development

Clone the repository:

```bash
git clone https://github.com/TechAkii/AK-E-Commerce-Clothing.git
```

Create and activate the virtual environment:

```bash
python -m venv venv
```

```powershell
venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the backend:

```bash
python app.py
```

# 📜 License

This project is licensed under the MIT License.

See the `LICENSE` file for more information.

---

# 👨‍💻 Author

**Akila Thikshana**

---
