"""
Database Initialization Script for Green SME Compliance Co-Pilot
Creates tables and inserts mock data for development/testing
"""

import sqlite3
import json
from datetime import datetime
import os


def init_database(db_path: str = "db.sqlite"):
    """Initialize SQLite database with schema and mock data"""
    
    # Remove existing database for clean start
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # User Profile Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS UserProfile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            city TEXT,
            postal_code TEXT,
            country TEXT DEFAULT 'DE',
            email TEXT,
            phone TEXT,
            IBAN TEXT,
            business_type TEXT,
            business_facts TEXT,
            employee_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Submission Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Submission (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userId INTEGER NOT NULL,
            intent TEXT NOT NULL,
            selected_forms TEXT,
            answers TEXT,
            files TEXT,
            status TEXT DEFAULT 'pending',
            audit_trail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (userId) REFERENCES UserProfile(id)
        )
    """)
    
    # Form Templates Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS FormTemplate (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            form_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            regulation TEXT,
            fields TEXT,
            embeddings BLOB,
            pdf_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Compliance Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ComplianceLog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER NOT NULL,
            regulation TEXT NOT NULL,
            article TEXT,
            action TEXT,
            status TEXT,
            evidence TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES Submission(id)
        )
    """)
    
    # Energy Data Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS EnergyData (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userId INTEGER NOT NULL,
            period TEXT,
            electricity_kwh REAL,
            gas_kwh REAL,
            heating_kwh REAL,
            renewable_kwh REAL,
            total_cost REAL,
            emissions_tco2e REAL,
            data_source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (userId) REFERENCES UserProfile(id)
        )
    """)
    
    print("Created tables: UserProfile, Submission, FormTemplate, ComplianceLog, EnergyData")
    
    # Insert mock user profiles
    mock_users = [
        (
            "Prime Bakery GmbH",
            "Flensburger Strasse 1",
            "Flensburg",
            "24937",
            "DE",
            "info@primebakery.de",
            "+49 461 123456",
            "DE89370400440532013000",
            "bakery",
            json.dumps({
                "industry": "food_production",
                "products": ["bread", "pastries", "cakes"],
                "certifications": ["organic"],
                "established": 1995
            }),
            12
        ),
        (
            "EcoTech Solutions UG",
            "Innovationsweg 42",
            "Berlin",
            "10115",
            "DE",
            "contact@ecotech.eu",
            "+49 30 987654",
            "DE89500700100123456789",
            "technology",
            json.dumps({
                "industry": "software_development",
                "products": ["sustainability_saas", "ai_consulting"],
                "certifications": ["ISO27001"],
                "established": 2020
            }),
            8
        )
    ]
    
    cursor.executemany("""
        INSERT INTO UserProfile 
        (name, address, city, postal_code, country, email, phone, IBAN, business_type, business_facts, employee_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, mock_users)
    
    print(f"Inserted {len(mock_users)} mock user profiles")
    
    # Insert mock energy data for Prime Bakery
    mock_energy = [
        (1, "2024-10", 3200.0, 1500.0, 800.0, 400.0, 1850.0, None, "smart_meter"),
        (1, "2024-09", 3100.0, 1450.0, 750.0, 380.0, 1820.0, None, "smart_meter"),
        (1, "2024-08", 2900.0, 1400.0, 700.0, 350.0, 1750.0, None, "smart_meter"),
    ]
    
    cursor.executemany("""
        INSERT INTO EnergyData 
        (userId, period, electricity_kwh, gas_kwh, heating_kwh, renewable_kwh, total_cost, emissions_tco2e, data_source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, mock_energy)
    
    print(f"Inserted {len(mock_energy)} mock energy records")
    
    # Insert form templates
    mock_forms = [
        (
            "vsme_snapshot",
            "CSRD VSME Snapshot",
            "sustainability",
            "CSRD_VSME",
            json.dumps({
                "company_name": "text",
                "reporting_period": "date",
                "total_energy_consumption_kwh": "number",
                "scope2_emissions_tco2e": "number",
                "methodology_note": "textarea",
                "reduction_actions": "textarea"
            }),
            None,
            "/templates/vsme_snapshot.pdf"
        ),
        (
            "gdpr_art30",
            "GDPR Article 30 Record",
            "data_protection",
            "GDPR_Art30",
            json.dumps({
                "controller_name": "text",
                "controller_contact": "text",
                "processing_purposes": "textarea",
                "data_categories": "textarea",
                "recipient_categories": "textarea",
                "retention_period": "text",
                "security_measures": "textarea"
            }),
            None,
            "/templates/gdpr_art30.pdf"
        ),
        (
            "eu_ai_act_risk",
            "EU AI Act Risk Assessment",
            "ai_compliance",
            "EU_AI_Act",
            json.dumps({
                "system_name": "text",
                "system_purpose": "textarea",
                "risk_category": "select",
                "high_risk_criteria": "checkbox",
                "prohibited_practices": "checkbox",
                "transparency_measures": "textarea",
                "human_oversight": "textarea"
            }),
            None,
            "/templates/eu_ai_act_risk.pdf"
        )
    ]
    
    cursor.executemany("""
        INSERT INTO FormTemplate 
        (form_id, name, category, regulation, fields, embeddings, pdf_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, mock_forms)
    
    print(f"Inserted {len(mock_forms)} form templates")
    
    conn.commit()
    conn.close()
    
    print(f"\nDatabase initialized successfully: {db_path}")
    print("\nMock data summary:")
    print(f"  - {len(mock_users)} user profiles")
    print(f"  - {len(mock_energy)} energy records")
    print(f"  - {len(mock_forms)} form templates")


if __name__ == "__main__":
    init_database()
