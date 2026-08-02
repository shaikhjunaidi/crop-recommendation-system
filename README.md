# Crop Recommendation System 🌱

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-005C84?style=for-the-badge&logo=mysql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)

A robust web application built with Django and Machine Learning that helps farmers and agricultural professionals recommend the most suitable crops based on soil nutrients and environmental conditions.

## 🚀 Features

- **Machine Learning Integration**: Uses a pre-trained Random Forest Classifier (`Crop_recommendation_RF.pkl`) to accurately predict crops.
- **Secure Authentication**: User registration and login system with encrypted passwords and profile management.
- **Admin Dashboard**: Comprehensive dashboard for administrators with visual charts (Chart.js) tracking system usage and predictions.
- **Prediction History**: Users can view, manage, and delete their previous crop predictions securely.
- **Modern UI**: Fully responsive and mobile-friendly interface built with Bootstrap 5.

## 🛠️ Technologies Used

- **Backend**: Python 3.12, Django 6.0
- **Machine Learning**: scikit-learn, Pandas, NumPy
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5, FontAwesome
- **Database**: MySQL

## 🧠 Machine Learning Model

The core of the prediction engine relies on an optimized Random Forest algorithm. It analyzes the following parameters to recommend the best crop:
- Nitrogen (N) ratio in soil
- Phosphorus (P) ratio in soil
- Potassium (K) ratio in soil
- Temperature (in Celsius)
- Humidity (relative percentage)
- pH value of the soil
- Rainfall (in mm)

## 📂 Folder Structure

```
crop-recommendation-system/
│
├── crop/                   # Main Django Project Settings
├── recommender/            # Django Application (Views, Models, URLs)
│   ├── ml/                 # Machine Learning Models & Loader
│   ├── static/             # CSS, JS, and Image files
│   └── templates/          # HTML Templates
│
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore file
├── manage.py               # Django execution script
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## ⚙️ Installation & Setup

Follow these steps to run the project locally.

### 1. Clone the repository
```bash
git clone https://github.com/shaikhjunaidi/crop-recommendation-system.git
cd crop-recommendation-system
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Rename `.env.example` to `.env` and fill in your database credentials:
```env
SECRET_KEY=your_super_secret_key_here
DEBUG=True

DB_NAME=crop_recommender
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

### 5. Setup the Database
Ensure MySQL is running, create the database, and run Django migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 7. Run the Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser!

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! 
Feel free to check the [issues page](https://github.com/shaikhjunaidi/crop-recommendation-system/issues) if you want to contribute.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Shaikh Junaid**
- LinkedIn: [Shaikh Junaid](https://www.linkedin.com/in/shaikh-junaid-a794a4405/)
- Email: [me.junaid.in@gmail.com](mailto:me.junaid.in@gmail.com)
