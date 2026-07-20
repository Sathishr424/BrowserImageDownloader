import asyncio
import json
import os
from aiohttp import web
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse
import requests

CONFIG_PATH = "config.json"

class Daemon:
    def __init__(self):
        data = self.fetchConfig()
        self.port = data["port"]
        self.downloadPath = data["download_directory"]

        if not os.path.exists(self.downloadPath):
            try:
                os.makedirs(self.downloadPath, exist_ok=True)
            except Exception as e:
                print("Error while create directory:", e)
                self.downloadPath = "~/"

    def fetchConfig(self):
        if not os.path.exists(CONFIG_PATH):
            return {
                "port": 5256,
                "download_directory": "/mnt/sat/Downloads/Images/"
            }
        with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
            return json.loads(file.read())

    def download_file(self, url: str, output_dir: str = ".") -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = Path(urlparse(url).path).name
        if not filename:
            raise ValueError(f"Couldn't determine filename from URL: {url}")

        output_path = output_dir / filename

        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        return output_path

    def download_files(self, urls: list[str], output_dir: str = ".", max_workers: int = 8):
        downloaded = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.download_file, url, output_dir): url
                for url in urls
            }

            for future in as_completed(futures):
                url = futures[future]
                try:
                    path = future.result()
                    print(f"✓ Downloaded {url} -> {path}")
                    downloaded.append(path)
                except Exception as e:
                    print(f"✗ Failed {url}: {e}")

        return downloaded


    async def downloadImages(self, request):
        data = await request.json()
        print("Received:", data)

        if "urls" not in data:
            return web.json_response({
                "error": "Urls needed to download the images"
            })
        
        self.download_files(data["urls"], self.downloadPath)

        return web.json_response({
            "status": "ok"
        })

    async def start(self):
        app = web.Application()
        app.router.add_post("/download_images", self.downloadImages)

        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, "127.0.0.1", self.port)

        try:
            await site.start()
        except OSError as e:
            if e.errno == 98:
                print(f"Port {self.port} is already in use.")
                return
            raise

        print(f"HTTP server listening on http://127.0.0.1:{self.port}")

        try:
            # Keep the daemon alive forever
            await asyncio.Event().wait()
        finally:
            print("Shutting down...")
            await runner.cleanup()


async def main():
    daemon = Daemon()
    await daemon.start()

if __name__ == "__main__":
    asyncio.run(main())
