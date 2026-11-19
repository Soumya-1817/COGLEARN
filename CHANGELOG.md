# COGLEARN Changelog

## [0.1.0] - 2026-11-19
### Added
- Initial full platform implementation
- Four mathematical cognitive models (Model 1-4)
- Complete university LMS
- Academic task queue with FIFO ordering
- Automatic calendar and deadline management
- Notification system
- Mentor intervention engine
- Institutional analytics portal
- React frontend for all 4 user roles
- Docker Compose development environment
- 33 unit tests for all 4 mathematical models (all passing)
- Demo seed data (Greenfield University)

### Models
- **Model 1**: Hierarchical Bayesian Gamma-Poisson capacity estimation
  - All parameters: v1.0-provisional
- **Model 2**: M/M/1 queueing workload assessment
- **Model 3**: ICAP-weighted workload quantification + 3-day causal moving average
  - All weights: v1.0-provisional  
- **Model 4**: Four-state HMM forward filter + IORI
  - All parameters: v1.0-provisional

### Notes
- All model parameters are explicitly marked PROVISIONAL
- IORI is structurally absent from all student-facing API schemas
- Tenant isolation enforced at application and database (RLS) level
