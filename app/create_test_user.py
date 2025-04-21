#!/usr/bin/env python3
# Direct database script to create test users - avoids import issues

import psycopg2
import uuid
import sys
from werkzeug.security import generate_password_hash

# Database connection parameters - make sure these match your .env file
DB_PARAMS = {
    'dbname': 'nutritrain_db',
    'user': 'postgres',
    'password': 'NutriMaxIAPassword',
    'host': 'db',
    'port': '5432'
}

def create_test_user():
    print("Creating test data directly with psycopg2...")
    
    conn = None
    cursor = None
    
    try:
        # Connect to the database
        conn = psycopg2.connect(**DB_PARAMS)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Create academy if it doesn't exist
        academy_id = "00000000-0000-0000-0000-000000000000"
        cursor.execute("""
            SELECT id FROM academias WHERE id = %s
        """, (academy_id,))
        
        academy_exists = cursor.fetchone()
        
        if not academy_exists:
            print("Creating test academy...")
            cursor.execute("""
                INSERT INTO academias (
                    id, nome, cnpj, contato_email, contato_telefone, 
                    status, codigo_acesso_membros, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
            """, (
                academy_id,
                "Academia Teste",
                "00.000.000/0001-00",
                "test@teste.com",
                "(00) 00000-0000",
                "ativo",
                "TEST123"
            ))
            print(f"Academy created with ID: {academy_id}")
        else:
            print(f"Using existing academy with ID: {academy_id}")
        
        # Create user if it doesn't exist
        user_id = "00000000-0000-0000-0000-000000000001"
        cursor.execute("""
            SELECT id FROM usuarios WHERE id = %s
        """, (user_id,))
        
        user_exists = cursor.fetchone()
        
        if not user_exists:
            print("Creating test user...")
            # Generate password hash - mimicking the User.set_password method
            password_hash = generate_password_hash("senha123")
            
            cursor.execute("""
                INSERT INTO usuarios (
                    id, nome, email, password_hash, academia_id,
                    status, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, NOW()
                )
            """, (
                user_id,
                "Usuário Teste",
                "usuario.teste@example.com",
                password_hash,
                academy_id,
                "ativo"
            ))
            print(f"User created with ID: {user_id}")
        else:
            print(f"User already exists with ID: {user_id}")
        
        # Commit the transaction
        conn.commit()
        print("Test data created successfully!")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error creating test data: {str(e)}")
        sys.exit(1)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    create_test_user()