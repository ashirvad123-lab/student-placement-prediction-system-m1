# Student Placement Prediction System

A learning project that demonstrates student record management and placement
classification with Flask, MySQL, and scikit-learn.

## Phase 2 foundation

This phase provides the dependency list, environment configuration template,
MySQL schema, synthetic data generator, and machine-learning train/predict
modules. The web interface and admin workflows are added in later phases.

The generated dataset is synthetic. Its evaluation scores demonstrate the
workflow only and must not be interpreted as real-world placement accuracy.

## Initial setup on Windows

1. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install packages:

   ```powershell
   py -m pip install --upgrade pip
   py -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set a private `FLASK_SECRET_KEY` and your
   MySQL connection settings. Do not share or commit `.env`.

4. In MySQL Workbench, open `database/schema.sql` and execute it. It creates
   `placement_db`, `users`, `students`, and `prediction_history`.

5. Generate the synthetic CSV and train/evaluate the candidate classifiers:

   ```powershell
   py data\generate_synthetic_data.py
   py -m placement.ml.train_model
   ```

The selected pipeline, measured metrics, and confusion-matrix chart are written
under `models/`. The model is selected from the actual held-out test results by
the F1-score for the `Placed` class, with accuracy used to break ties.
