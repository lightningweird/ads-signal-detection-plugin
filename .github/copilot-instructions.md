<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Signal Detection Plugin Project

This is a Python-based signal detection plugin designed for real-time data processing and anomaly detection. The project features:

- Multi-source data ingestion (WebSocket, REST API, Kafka, Redis)
- Hot-swappable deserializers with auto-format detection  
- Advanced backpressure handling with disk spillover
- GPU/CPU resource awareness for detectors
- Plugin architecture with dynamic loading
- Direct integration with anomaly detection memory systems

## Architecture Guidelines

- Follow the modular plugin architecture pattern
- Use dependency injection for testability
- Implement proper error handling and logging
- Ensure thread-safe operations for concurrent processing
- Use type hints throughout the codebase
- Follow Python PEP 8 style guidelines

## Key Components

- `src/core/`: Core interfaces, models, and configuration
- `src/sources/`: Data source implementations (WebSocket, REST, Kafka, Redis)
- `src/pipeline/`: Stream processing and data pipeline components
- `src/detectors/`: Anomaly detection algorithms (statistical, ML, transformer-based)
- `src/plugins/`: Plugin management and dynamic loading system
- `src/memory/`: Memory interface for anomaly detection systems
- `src/monitoring/`: Health checks and metrics collection

## Integration Notes

The plugin is designed to integrate directly with the ads-anomaly-detection system and supports both direct function calls and Redis pub/sub for distributed deployments.
