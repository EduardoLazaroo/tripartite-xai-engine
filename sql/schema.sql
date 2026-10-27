CREATE DATABASE IF NOT EXISTS evidence_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE evidence_db;

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id VARCHAR(36) PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS images (
    image_id VARCHAR(36) PRIMARY KEY,
    dataset_name TEXT,
    source_uri TEXT,
    original_width INT,
    original_height INT,
    checksum TEXT,
    format TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS noise_profiles (
    noise_id VARCHAR(36) PRIMARY KEY,
    noise_type TEXT NOT NULL,
    intensity FLOAT,
    kernel_size TEXT,
    parameters JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS class_labels (
    label_id VARCHAR(36) PRIMARY KEY,
    label_name TEXT NOT NULL,
    hierarchy_path TEXT,
    description TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS media_assets (
    media_asset_id VARCHAR(36) PRIMARY KEY,
    asset_type TEXT NOT NULL,
    storage_uri TEXT NOT NULL,
    checksum TEXT,
    format TEXT,
    width INT,
    height INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS inferences (
    inference_id VARCHAR(36) PRIMARY KEY,
    image_id VARCHAR(36),
    experiment_id VARCHAR(36),
    noise_id VARCHAR(36),
    predicted_label_id VARCHAR(36),
    confidence FLOAT,
    probabilities JSON,
    preprocessing_steps JSON,
    model_version TEXT,
    inference_duration_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (image_id) REFERENCES images(image_id) ON DELETE CASCADE,
    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    FOREIGN KEY (noise_id) REFERENCES noise_profiles(noise_id),
    FOREIGN KEY (predicted_label_id) REFERENCES class_labels(label_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS embeddings (
    embedding_id VARCHAR(36) PRIMARY KEY,
    inference_id VARCHAR(36),
    vector_db_id TEXT NOT NULL,
    dimension INT NOT NULL,
    norm FLOAT,
    embedding_metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (inference_id) REFERENCES inferences(inference_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS gradcams (
    gradcam_id VARCHAR(36) PRIMARY KEY,
    inference_id VARCHAR(36),
    media_asset_id VARCHAR(36),
    activation_distribution JSON,
    region_stats JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (inference_id) REFERENCES inferences(inference_id) ON DELETE CASCADE,
    FOREIGN KEY (media_asset_id) REFERENCES media_assets(media_asset_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS similarity_records (
    similarity_id VARCHAR(36) PRIMARY KEY,
    query_inference_id VARCHAR(36),
    target_inference_id VARCHAR(36),
    embedding_similarity FLOAT,
    gradcam_overlap FLOAT,
    distance_metric TEXT,
    `rank` INT,
    retrieval_time_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (query_inference_id) REFERENCES inferences(inference_id) ON DELETE CASCADE,
    FOREIGN KEY (target_inference_id) REFERENCES inferences(inference_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS audit_trail (
    audit_id VARCHAR(36) PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id VARCHAR(36),
    action TEXT NOT NULL,
    performed_by TEXT,
    user_agent TEXT,
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS perturbation_comparisons (
    comparison_id VARCHAR(36) PRIMARY KEY,
    baseline_inference_id VARCHAR(36),
    perturbed_inference_id VARCHAR(36),
    noise_type TEXT NOT NULL,
    confidence_delta FLOAT,
    class_changed TINYINT(1),
    gradcam_overlap FLOAT,
    gradcam_correlation FLOAT,
    embedding_similarity FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (baseline_inference_id) REFERENCES inferences(inference_id) ON DELETE CASCADE,
    FOREIGN KEY (perturbed_inference_id) REFERENCES inferences(inference_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS benchmark_runs (
    benchmark_id VARCHAR(36) PRIMARY KEY,
    experiment_id VARCHAR(36),
    num_images INT,
    num_variants INT,
    total_persistence_ms INT,
    avg_retrieval_ms FLOAT,
    total_storage_bytes BIGINT,
    metrics JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX IF NOT EXISTS idx_inferences_experiment ON inferences(experiment_id);
CREATE INDEX IF NOT EXISTS idx_inferences_image ON inferences(image_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_inference ON embeddings(inference_id);
CREATE INDEX IF NOT EXISTS idx_gradcams_inference ON gradcams(inference_id);
CREATE INDEX IF NOT EXISTS idx_media_asset_type ON media_assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_perturbation_noise ON perturbation_comparisons(noise_type);
CREATE INDEX IF NOT EXISTS idx_perturbation_baseline ON perturbation_comparisons(baseline_inference_id);
CREATE INDEX IF NOT EXISTS idx_audit_trail_entity ON audit_trail(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_trail(action);
