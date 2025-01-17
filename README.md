# Local Deployment Guide for Médiathèque Application

## Prerequisites

1. **Install Docker Desktop**
   - Download from https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop
   - Verify installation:
     ```bash
     docker --version
     docker-compose --version
     ```

2. **Clone the Project**
   Create a new directory and clone all the necessary files:
   ```bash
   mkdir mediatheque
   cd mediatheque
   ```

## Project Setup

1. **Create Project Structure**
   ```
   mediatheque/
   ├── app/
   │   ├── __init__.py
   │   ├── auth.py
   │   ├── schemas.py
   │   └── error_handlers.py
   |   |__ routes
   |          |__ subscribers.py
   |          |__ loans.py
   |          |__ documents.py
   ├── static/
   │   ├── css/
   │   └── js/
   ├── templates/
   │   └── index.html
   ├── scripts/
   │   └── generate_test_data.py
   |
   |__ app.py
   ├── Dockerfile
   ├── docker-compose.yml
   ├── requirements.txt
   ├── .env
   └── .gitignore
   ```

2. **Copy Configuration Files**
   Copy all the previously created files (from earlier artifacts) into their respective locations in the project structure.

## Deployment Steps

1. **Build and Start Services**
   ```bash
   # Start all services
   docker-compose up --build -d
   ```

2. **Verify Services**
   ```bash
   # Check if containers are running
   docker-compose ps
   ```

3. **Generate Test Data**
   ```bash
   # Connect to web container and run the script
   docker-compose exec web python scripts/generate_test_data.py
   ```

## Accessing the Application

- **Web Application**: http://localhost:5000
- **MongoDB Admin Interface**: http://localhost:8081
  - Username: admin
  - Password: admin123

## User Credentials (After generating test data)

- **Admin User**:
  - Email: admin@mediatheque.com
  - Password: admin123

- **Regular Users**:
  - Email: john.doe@mediatheque.com
  - Email: jane.smith@mediatheque.com
  - Email: robert.johnson@mediatheque.com
  - Password for all regular users: user123

## Maintenance Commands

```bash
# View application logs
docker-compose logs -f web

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Stop services and remove volumes (will delete database data)
docker-compose down -v

# Check container status
docker-compose ps
```

## Troubleshooting

1. **If ports are already in use**:
   - Check if any other services are using ports 5000, 27017, or 8081
   - Stop those services or modify the port mappings in docker-compose.yml

2. **If containers fail to start**:
   ```bash
   # Check detailed logs
   docker-compose logs
   ```

3. **If database connection fails**:
   - Ensure MongoDB container is running
   - Check the MONGO_URI in .env file
   - Verify network connectivity between containers

4. **If changes don't appear**:
   ```bash
   # Rebuild and restart containers
   docker-compose down
   docker-compose up --build -d
   ```

5. **Test unit**:
   ```bash
   # Run tests:
   #These tests cover:
   #CRUD operations for all entities
   #Pagination for documents
   #Business rules cannot delete loaned documents
   #Date handling in loans
   #Relationships between entities
   #Error cases

   pytest
   ```