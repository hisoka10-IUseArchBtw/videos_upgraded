from minio import Minio
import inspect

m = Minio("localhost:9000", access_key="minioadmin", secret_key="minioadmin", secure=False)
print(dir(m))
