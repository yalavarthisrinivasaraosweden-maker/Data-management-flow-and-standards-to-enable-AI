# Robust Database Storage System

This document describes the robust database storage implementations for the AM Experimental Data Management Pipeline.

## Database Options

The system supports two robust database solutions:

1. **PostgreSQL** - Relational database with ACID guarantees
2. **MongoDB** - NoSQL document database for flexible schemas

## PostgreSQL Implementation

### Features

- ✅ **ACID Compliance**: Full transactional support
- ✅ **Connection Pooling**: Efficient connection management
- ✅ **SQLAlchemy ORM**: Type-safe database operations
- ✅ **Automatic Migrations**: Schema versioning and updates
- ✅ **Indexes**: Optimized query performance
- ✅ **Foreign Keys**: Data integrity constraints
- ✅ **Health Checks**: Connection monitoring

### Setup

1. **Install PostgreSQL** (if not already installed):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql
   
   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

2. **Create Database**:
   ```bash
   sudo -u postgres psql
   CREATE DATABASE am_data_db;
   CREATE USER am_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE am_data_db TO am_user;
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements_postgres.txt
   ```

4. **Configure Connection**:
   ```bash
   export DATABASE_URL="postgresql://am_user:your_password@localhost:5432/am_data_db"
   ```

5. **Run Migrations**:
   ```bash
   python database_migrations.py
   ```

6. **Start Server**:
   ```bash
   python am_data_pipeline_postgres.py
   ```

### Connection Pooling

The PostgreSQL implementation uses SQLAlchemy's connection pooling:

- **Pool Size**: 10 connections
- **Max Overflow**: 20 additional connections
- **Pool Recycle**: 1 hour (prevents stale connections)
- **Pool Pre-ping**: Verifies connections before use

### Database Schema

The schema includes:
- **experiments** - Main experiment records
- **process_parameters** - AM process settings
- **geometry_data** - Build geometry information
- **quality_metrics** - Measured quality characteristics
- **sensor_data** - Time-series sensor readings
- **ml_features** - Precomputed ML features

All tables include:
- Primary keys and foreign keys
- Indexes on frequently queried fields
- Timestamps (created_at, updated_at)
- Cascade delete for data integrity

## MongoDB Implementation

### Features

- ✅ **Document Storage**: Flexible schema for varying data structures
- ✅ **Horizontal Scaling**: Built-in sharding support
- ✅ **Aggregation Pipeline**: Powerful data processing
- ✅ **Indexes**: Optimized query performance
- ✅ **Connection Pooling**: Efficient connection management
- ✅ **Health Checks**: Connection monitoring

### Setup

1. **Install MongoDB** (if not already installed):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install mongodb
   
   # macOS
   brew install mongodb-community
   
   # Windows
   # Download from https://www.mongodb.com/try/download/community
   ```

2. **Start MongoDB**:
   ```bash
   # Linux
   sudo systemctl start mongod
   
   # macOS
   brew services start mongodb-community
   
   # Windows
   # Start MongoDB service from Services
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements_mongodb.txt
   ```

4. **Configure Connection**:
   ```bash
   export MONGODB_URL="mongodb://localhost:27017/"
   export MONGODB_DATABASE="am_data_db"
   ```

5. **Start Server**:
   ```bash
   python am_data_pipeline_mongodb.py
   ```

### Connection Pooling

The MongoDB implementation uses PyMongo's connection pooling:

- **Max Pool Size**: 50 connections
- **Min Pool Size**: 10 connections
- **Connection Timeout**: 5 seconds
- **Server Selection Timeout**: 5 seconds

### Collections

The MongoDB implementation uses:
- **experiments** - Main experiment documents (with nested subdocuments)
- **sensor_data** - Time-series sensor readings
- **ml_features** - Precomputed ML features

All collections include:
- Indexes on frequently queried fields
- Unique constraints where needed
- Compound indexes for complex queries

## Docker Setup

Both databases can be run using Docker Compose:

```bash
# Start PostgreSQL and API
docker-compose up postgres api_postgres

# Start MongoDB and API
docker-compose up mongodb api_mongodb

# Start both databases
docker-compose up
```

## Comparison

| Feature | PostgreSQL | MongoDB |
|---------|-----------|---------|
| **Data Model** | Relational (Tables) | Document (Collections) |
| **Schema** | Fixed Schema | Flexible Schema |
| **ACID** | Full ACID | Multi-document ACID |
| **Joins** | Native SQL Joins | Aggregation Pipeline |
| **Scalability** | Vertical + Horizontal | Horizontal (Sharding) |
| **Query Language** | SQL | MongoDB Query Language |
| **Best For** | Structured data, complex queries | Flexible schemas, rapid development |

## Choosing a Database

### Choose PostgreSQL if:
- You need strict data integrity
- You have complex relational queries
- You prefer SQL
- You need ACID transactions across multiple tables
- Your data structure is well-defined

### Choose MongoDB if:
- You have varying data structures
- You need rapid schema evolution
- You prefer document-based storage
- You need horizontal scaling
- Your queries are primarily document-based

## Migration Between Databases

To migrate data between databases:

1. **Export from source database**:
   ```bash
   # PostgreSQL
   pg_dump -U username am_data_db > backup.sql
   
   # MongoDB
   mongoexport --db am_data_db --collection experiments --out experiments.json
   ```

2. **Import to target database**:
   ```bash
   # PostgreSQL
   psql -U username am_data_db < backup.sql
   
   # MongoDB
   mongoimport --db am_data_db --collection experiments --file experiments.json
   ```

## Performance Optimization

### PostgreSQL
- Use connection pooling (already configured)
- Create indexes on frequently queried columns (already done)
- Use prepared statements (SQLAlchemy handles this)
- Monitor query performance with `EXPLAIN ANALYZE`

### MongoDB
- Create indexes on frequently queried fields (already done)
- Use compound indexes for complex queries
- Monitor query performance with `.explain()`
- Use aggregation pipeline for complex operations

## Backup and Recovery

### PostgreSQL Backup
```bash
# Full backup
pg_dump -U username am_data_db > backup_$(date +%Y%m%d).sql

# Restore
psql -U username am_data_db < backup_20240101.sql
```

### MongoDB Backup
```bash
# Full backup
mongodump --db am_data_db --out /backup/$(date +%Y%m%d)

# Restore
mongorestore --db am_data_db /backup/20240101/am_data_db
```

## Health Monitoring

Both implementations include health check endpoints:

```bash
# Check API health
curl http://localhost:8000/health
```

The health check verifies:
- Database connectivity
- Connection pool status
- Server timestamp

## Troubleshooting

### PostgreSQL Connection Issues
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check connection string format
- Verify user permissions
- Check firewall settings

### MongoDB Connection Issues
- Verify MongoDB is running: `sudo systemctl status mongod`
- Check connection string format
- Verify authentication credentials
- Check network connectivity

## Environment Variables

Create a `.env` file (see `.env.example`):

```bash
# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/am_data_db

# MongoDB
MONGODB_URL=mongodb://localhost:27017/
MONGODB_DATABASE=am_data_db
```

Load environment variables:
```bash
export $(cat .env | xargs)
```

## Security Best Practices

1. **Use Environment Variables**: Never hardcode credentials
2. **Enable SSL/TLS**: Use encrypted connections in production
3. **Limit Permissions**: Grant only necessary database permissions
4. **Regular Backups**: Schedule automated backups
5. **Monitor Access**: Log and monitor database access
6. **Update Regularly**: Keep database software updated

## Production Deployment

For production deployment:

1. Use managed database services (AWS RDS, MongoDB Atlas)
2. Enable SSL/TLS connections
3. Configure automated backups
4. Set up monitoring and alerting
5. Use read replicas for scaling
6. Implement connection limits
7. Enable query logging for optimization
