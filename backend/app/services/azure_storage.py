import os
import logging
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

LOCAL_STORAGE_ROOT = Path(getattr(settings, 'LOCAL_BLOB_STORAGE_DIR', 'storage_blobs'))


def _is_configured() -> bool:
    conn_str = settings.AZURE_STORAGE_CONNECTION_STRING
    if conn_str and 'AccountName=<' not in conn_str and len(conn_str) > 20:
        return True
    if getattr(settings, 'AZURE_STORAGE_ACCOUNT_NAME', '') and getattr(settings, 'AZURE_STORAGE_ACCOUNT_KEY', ''):
        return True
    return False


async def ensure_containers_exist() -> List[str]:
    containers = [
        settings.AZURE_STORAGE_CONTAINER_DOCUMENTS,
        getattr(settings, 'AZURE_STORAGE_CONTAINER_TIMETABLES', 'timetable-uploads'),
        getattr(settings, 'AZURE_STORAGE_CONTAINER_STUDENT_FILES', 'student-uploads'),
        getattr(settings, 'AZURE_STORAGE_CONTAINER_RAG', 'rag-knowledge-base'),
    ]

    if not _is_configured():
        for c in containers:
            (LOCAL_STORAGE_ROOT / c).mkdir(parents=True, exist_ok=True)
        logger.info('Local storage blob containers initialized under %s', LOCAL_STORAGE_ROOT)
        return containers

    try:
        from azure.storage.blob.aio import BlobServiceClient
        from azure.storage.blob import ContentSettings
        async with BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING) as client:
            for container_name in containers:
                container_client = client.get_container_client(container_name)
                if not await container_client.exists():
                    await container_client.create_container()
                    logger.info('Created Azure Blob Storage container: %s', container_name)
        return containers
    except Exception as exc:
        logger.warning('Failed to provision Azure containers: %s', exc)
        return containers


async def upload_blob(
    file_name: str,
    file_content: bytes,
    container_name: Optional[str] = None,
    content_type: str = 'application/octet-stream',
    metadata: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    target_container = container_name or settings.AZURE_STORAGE_CONTAINER_DOCUMENTS
    meta = metadata or {}
    meta.setdefault('uploaded_at', datetime.datetime.utcnow().isoformat())

    if not _is_configured():
        container_dir = LOCAL_STORAGE_ROOT / target_container
        container_dir.mkdir(parents=True, exist_ok=True)
        local_file_path = container_dir / file_name
        with open(local_file_path, 'wb') as f:
            f.write(file_content)

        file_url = 'http://localhost:8000/static/blobs/' + target_container + '/' + file_name
        logger.info('Uploaded blob locally: container=%s file=%s size=%d', target_container, file_name, len(file_content))
        return {
            'success': True,
            'blob_name': file_name,
            'container': target_container,
            'url': file_url,
            'size_bytes': len(file_content),
            'content_type': content_type,
            'metadata': meta,
            'is_azure': False,
        }

    try:
        from azure.storage.blob.aio import BlobServiceClient
        from azure.storage.blob import ContentSettings
        async with BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING) as client:
            container_client = client.get_container_client(target_container)
            if not await container_client.exists():
                await container_client.create_container()

            blob_client = container_client.get_blob_client(file_name)
            await blob_client.upload_blob(
                file_content,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type),
                metadata=meta,
            )
            blob_url = blob_client.url
            logger.info('Uploaded blob to Azure Storage: container=%s file=%s url=%s', target_container, file_name, blob_url)
            return {
                'success': True,
                'blob_name': file_name,
                'container': target_container,
                'url': blob_url,
                'size_bytes': len(file_content),
                'content_type': content_type,
                'metadata': meta,
                'is_azure': True,
            }
    except Exception as exc:
        logger.error('Azure Blob Storage upload error for %s: %s', file_name, exc)
        return {
            'success': False,
            'error': str(exc),
            'blob_name': file_name,
            'container': target_container,
        }


async def download_blob(file_name: str, container_name: Optional[str] = None) -> Optional[bytes]:
    target_container = container_name or settings.AZURE_STORAGE_CONTAINER_DOCUMENTS

    if not _is_configured():
        local_path = LOCAL_STORAGE_ROOT / target_container / file_name
        if local_path.exists():
            return local_path.read_bytes()
        return None

    try:
        from azure.storage.blob.aio import BlobServiceClient
        from azure.storage.blob import ContentSettings
        async with BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING) as client:
            blob_client = client.get_blob_client(container=target_container, blob=file_name)
            stream = await blob_client.download_blob()
            return await stream.readall()
    except Exception as exc:
        logger.error('Azure Blob Storage download failed for %s: %s', file_name, exc)
        return None


async def list_documents(container_name: Optional[str] = None) -> List[Dict[str, Any]]:
    target_container = container_name or settings.AZURE_STORAGE_CONTAINER_DOCUMENTS

    if not _is_configured():
        container_dir = LOCAL_STORAGE_ROOT / target_container
        if not container_dir.exists():
            return [
                {'name': 'Academic-Regulations-2024-25.pdf', 'size': 1245320, 'last_modified': '2024-08-01T00:00:00Z', 'container': target_container, 'url': 'https://mock-storage.blob.core.windows.net/university-documents/Academic-Regulations-2024-25.pdf', 'is_azure': False},
                {'name': 'Hostel-Rules-2024.pdf', 'size': 890234, 'last_modified': '2024-07-15T00:00:00Z', 'container': target_container, 'url': 'https://mock-storage.blob.core.windows.net/university-documents/Hostel-Rules-2024.pdf', 'is_azure': False},
                {'name': 'Examination-Ordinance-2024.pdf', 'size': 654321, 'last_modified': '2024-06-20T00:00:00Z', 'container': target_container, 'url': 'https://mock-storage.blob.core.windows.net/university-documents/Examination-Ordinance-2024.pdf', 'is_azure': False},
            ]
        results = []
        for p in container_dir.iterdir():
            if p.is_file():
                stat = p.stat()
                results.append({
                    'name': p.name,
                    'size': stat.st_size,
                    'last_modified': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'container': target_container,
                    'url': 'http://localhost:8000/static/blobs/' + target_container + '/' + p.name,
                    'is_azure': False,
                })
        return results

    try:
        from azure.storage.blob.aio import BlobServiceClient
        from azure.storage.blob import ContentSettings
        async with BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING) as client:
            container_client = client.get_container_client(target_container)
            blobs = []
            async for blob in container_client.list_blobs(include=['metadata']):
                blobs.append({
                    'name': blob.name,
                    'size': blob.size,
                    'last_modified': blob.last_modified.isoformat() if blob.last_modified else None,
                    'content_type': blob.content_settings.content_type if blob.content_settings else None,
                    'metadata': blob.metadata or {},
                    'container': target_container,
                    'url': 'https://' + client.account_name + '.blob.core.windows.net/' + target_container + '/' + blob.name,
                    'is_azure': True,
                })
            return blobs
    except Exception as exc:
        logger.error('Azure Blob Storage list failed: %s', exc)
        return []


async def store_document_for_rag(
    file_name: str,
    file_content: bytes,
    category: str = 'policy',
    content_type: str = 'application/pdf',
    metadata: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    meta = metadata or {}
    meta.update({
        'rag_indexable': 'true',
        'category': category,
        'uploaded_at': datetime.datetime.utcnow().isoformat(),
    })

    res1 = await upload_blob(
        file_name=file_name,
        file_content=file_content,
        container_name=settings.AZURE_STORAGE_CONTAINER_DOCUMENTS,
        content_type=content_type,
        metadata=meta,
    )

    rag_container = getattr(settings, 'AZURE_STORAGE_CONTAINER_RAG', 'rag-knowledge-base')
    await upload_blob(
        file_name=file_name,
        file_content=file_content,
        container_name=rag_container,
        content_type=content_type,
        metadata=meta,
    )

    res1['rag_container'] = rag_container
    res1['rag_ready'] = True
    return res1


async def upload_document(file_name: str, file_content: bytes, content_type: str = 'application/pdf') -> dict:
    return await upload_blob(file_name, file_content, container_name=settings.AZURE_STORAGE_CONTAINER_DOCUMENTS, content_type=content_type)