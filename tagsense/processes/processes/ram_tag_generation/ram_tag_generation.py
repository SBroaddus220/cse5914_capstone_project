# -*- coding: utf-8 -*-

"""
Example algorithm to generate RAM tags.
"""

# **** IMPORTS ****
import sys
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Tuple, Optional

from tagsense.processes.app_process import AppProcess
from tagsense.data_structures.app_data_structure import AppDataStructure
from tagsense.data_structures.data_structures.file_table.file_table import Files
from tagsense.data_structures.data_structures.ram_generated_tags.ram_generated_tags import RamGeneratedTags

# **** LOGGING ****
logger = logging.getLogger(__name__)

class RAMGenerateTags(AppProcess):
    """Generates tags for RAM data."""
    name: str = "ram_generate_tags"
    input: AppDataStructure = Files
    output: AppDataStructure = RamGeneratedTags
    requires_installation: bool = True
    
    @classmethod
    def execute(cls, input_data_key: str) -> Tuple[str, Optional[dict]]:
        print(f"Running {cls.name}...\n")
            
        # ****
        # Check if the process has already been run
        existing = cls.output.read_by_input_key(input_data_key)
        reference_msg = f"{input_data_key} from {cls.input.name}"
        if existing:
            msg = f"{cls.name} already executed for {reference_msg}. Skipping."
            print(msg + "\n")
            return (msg, None)
        
        # ****
        # Otherwise, create a new record
        file_record = cls.input.read_by_entry_key(input_data_key)
        if not file_record:
            msg = "No matching file record found in database."
            print(msg + "\n")
            return (msg, None)
        
        file_path: str = Path(file_record["file_path"]).as_posix()
        
        tags = cls.generate_tags(file_path)
        data = {"tags": tags}
        cls.output.create_entry(
            data=data,
            process=cls,
            input_data_structure=cls.input,
            input_data_key=input_data_key
        )
        
        msg = f"{cls.name} process completed for {reference_msg}."
        print(msg + "\n")
        return (msg, data)

    @classmethod
    def install(cls) -> None:
        """Installs the process."""
        super().install()

        path = Path(__file__).resolve().parent
        print(f"[Installer] Installing in: {path}")

        poetry_executable = shutil.which("poetry")
        if poetry_executable is None:
            raise FileNotFoundError("Poetry executable not found.")

        try:
            # First install command
            cls._run_and_stream([
                sys.executable, "-m", "pip", "install", "git+https://github.com/xinyu1205/recognize-anything.git"
            ])

            # Second install command
            cls._run_and_stream([
                poetry_executable, "install"
            ], cwd=path.as_posix())

            print("[Installer] Optional support installed successfully.")

        except subprocess.CalledProcessError as e:
            print("[Installer] Installation failed:", e)

    @staticmethod
    def _run_and_stream(cmd, cwd=None):
        """Runs a command and prints output line-by-line to stdout."""
        print(f"[Running] {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd,
            bufsize=1
        )

        # Stream output line-by-line
        for line in process.stdout:
            print(line.rstrip())

        returncode = process.wait()
        if returncode != 0:
            raise subprocess.CalledProcessError(returncode, cmd)
            
    @classmethod
    def generate_tags(cls, file_path) -> str:
        from ram.models import ram_plus
        from PIL import Image
        import torch
        from ram import get_transform
        from ram import inference_ram as inference
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = ram_plus(
            pretrained = (Path(__file__).parent / "ram_plus_swin_large_14m.pth").as_posix(),
            image_size = 384,
            vit = 'swin_l'
        )
        
        model.eval()
        model = model.to(device)
        transform = get_transform(image_size=384)
        image = transform(Image.open(file_path)).unsqueeze(0).to(device)
        res = inference(image, model)
        return res[0]
            
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.")
