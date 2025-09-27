# 📘 Image MetaCleaner - Documentation
## 1. Description of the Software
MetaCleaner is a web application that allows users to upload image files, inspect metadata, scrub sensitive EXIF data (e.g., GPS location, camera information) using ExifTool, and download the cleaned result. Users can also review a history of their cleaned files (filename and size deltas only).

---

### Main Features
- User authentication (signup/login/logout).
- Image upload with metadata preview before and after cleaning.
- Cleaner microservice that isolates the EXIF removal process.
- Download of sanitized images.
- History view showing previous clean operations per user.
- Persistent MySQL storage for users and history records.

---
## 2. Software Architecture Design
### Components & Responsabilities
- Auth microservice
    - Handles signup/login/logout.
    - Validates credentials.
    - Hashes passwords before storing them.
    - Used DB for user data.
- App microservice (Frontend/UI)
    - Handles web requests from users.
    - Provides pages: login, signup, index, history.
    - Orchestrates requests: uploads files, calls cleaner, stores results in DB.
- Cleaner microservice
    - Stateless microservice wrapping `exiftool`.
    - Provides REST API endpoints:
        - `/metadata` -> returns metadata of an image.
        - `/clean` -> removes metadata and returns cleaned file (Base64).
- Database microservice (MySQL)
    - Stores user accounts and file history.
    - Runs as stateful service with persistent volume claim (PVC).

## 🛠️ Setup

### Clone
~~~bash
git clone https://github.com/Ahmed-2-S/image-MetaCleaner.git
cd image-MetaCleaner
~~~

### Configure Kubernetes Secrets
1. Copy the template to a local file and fill in real values (the copy stays untracked by Git):
   ~~~bash
   cp k8s/secrets.template.yaml k8s/secrets.local.yaml
   nano k8s/secrets.local.yaml    # or open with your preferred editor
   ~~~
   Replace each REPLACE_* placeholder with your actual database credentials, API key, and a strong Flask SECRET_KEY.
2. Apply the secret before deploying workloads:
   ~~~bash
   kubectl apply -f k8s/secrets.local.yaml
   ~~~
3. Alternatively generate the secret on the fly (idempotent example):
   ~~~bash
   kubectl create secret generic metacleaner-secrets \
     --namespace metacleaner \
     --from-literal=DB_HOST=metacleaner-db \
   --from-literal=DB_PORT=3306 \
   --from-literal=DB_USER=REPLACE_DB_USERNAME \
   --from-literal=DB_PASSWORD=REPLACE_DB_PASSWORD \
   --from-literal=DB_NAME=REPLACE_DB_NAME \
   --from-literal=CLEANER_API_KEY=REPLACE_CLEANER_API_KEY \
   --from-literal=SECRET_KEY=REPLACE_FLASK_SECRET_KEY \
   --dry-run=client -o yaml | kubectl apply -f -
 ~~~

### Optional: Local Docker Compose
1. Copy the template to keep secrets local:
   ~~~bash
   cp docker-compose.template.yml docker-compose.yml
   nano docker-compose.yml  # fill in REPLACE_* values
   ~~~
2. The generated `docker-compose.yml` is ignored by Git, so credentials never leave your machine.
