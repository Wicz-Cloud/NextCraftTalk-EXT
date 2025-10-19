# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-18

### Added
- **Simplified Architecture**: Direct x.ai integration eliminating need for local data storage
- **Reduced Dependencies**: Removed ChromaDB, vector databases, and ML libraries
- **Faster Deployment**: No data scraping or vector database building required
- **Lower Resource Usage**: Eliminated memory-intensive local AI processing

### Removed
- **RAG Pipeline**: Replaced with direct x.ai queries for all responses
- **Wiki Scraper**: No longer needed as x.ai provides comprehensive knowledge
- **Vector Database**: ChromaDB and related vector storage components removed
- **Response Caching**: Cache system removed in favor of x.ai's native capabilities
- **Data Scraping**: All wiki scraping functionality and related code removed
- **ML Dependencies**: Sentence transformers, torch, and related libraries removed

### Changed
- **API Endpoints**: Removed /clear-cache endpoint and updated health checks
- **Configuration**: Removed RAG and cache configuration options
- **Documentation**: Updated to reflect simplified x.ai-only architecture

## [1.0.0] - 2025-10-18

### Added
- **x.ai Integration**: Complete migration from Ollama to x.ai API for enhanced AI capabilities
- **Visual Database Explorer**: New tool for exploring vector database contents
- **Dynamic Network Configuration**: Docker network name now configurable via environment variables
- **Enhanced Deployment Script**: Unified deploy-and-setup.sh with conflict detection
- **Nextcloud Talk Webhook Integration**: Secure webhook handling with HMAC-SHA256 signature verification
- **Log Rotation**: Automatic log rotation with Docker volume mounting
- **Cache Management**: Clear-cache endpoint and improved cache performance
- **Security Enhancements**: Comprehensive security policy and contributor guidelines
- **Code Quality Tools**: Pre-commit hooks, black formatting, mypy type checking, and bandit security scanning

### Changed
- **API Architecture**: Refactored to modern Python structure with src/ layout
- **Performance Optimization**: RAG pipeline optimizations for faster chat responses
- **Logging**: Suppressed debug logging and ChromaDB telemetry messages
- **Documentation**: Comprehensive README updates and deployment guides

### Fixed
- **Infinite Message Loop**: Bot now ignores its own messages
- **SQLite Database Mounting**: Fixed Docker volume mounting issues
- **Import Issues**: Resolved configuration validation and import problems
- **Code Formatting**: Consistent black formatting across codebase
- **Timeout Values**: Corrected timeout configurations

### Removed
- **Ollama Integration**: Replaced with x.ai API
- **Large Data Files**: Removed from version control (now using Git LFS)
- **Duplicate Docker Files**: Cleaned up redundant docker-compose.yml files

### Security
- **HMAC-SHA256 Verification**: Implemented for Nextcloud webhook security
- **Security Policy**: Added comprehensive security reporting guidelines
- **Code Security Scanning**: Integrated bandit for automated security checks

## [0.1.0] - 2025-10-05

### Added
- **Initial Minecraft Bot**: Basic chatbot functionality with Nextcloud Talk integration
- **Wiki Scraper**: Automated Minecraft wiki data collection system
- **Vector Database**: ChromaDB integration for knowledge storage and retrieval
- **RAG Pipeline**: Retrieval-augmented generation for context-aware responses
- **RESTful API**: Endpoints for bot interaction and management
- **Docker Deployment**: Complete containerization with docker-compose
- **Configuration Management**: Environment-based configuration system
- **Cache System**: SQLite-based recipe cache manager
- **Testing Suite**: Comprehensive test coverage and maintenance scripts

### Changed
- **Project Structure**: Organized codebase with clear separation of concerns
- **Deployment**: Streamlined setup and deployment processes with automated scripts

### Fixed
- **Web Scraper**: Fixed wiki data extraction and processing
- **Backend Integration**: Resolved API communication issues
- **Module Loading**: Fixed import and module resolution problems
- **Database Operations**: SQLite integration and data persistence
