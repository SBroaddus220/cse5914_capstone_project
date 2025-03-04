# TagSense
CSE5914 Project by Team Prompt Engineers

## Description
This project is a tag-based recommendation system that generates meaningful metadata for media files and enables intuitive search and discovery, offering a more efficient alternative to traditional browsing methods.

## Getting Started

### Prerequisites

1. Python 3.11+
```bash
python --version  # Windows
python3 --version  # Linux
```

2. Poetry
- Poetry is the chosen package manager for the project. Other package managers may work, but are not directly supported.
    1. **Installation**
    Please refer to the [official Poetry website](https://python-poetry.org/docs/#installation) for installation instructions.

    2. **Verify Installation**
    ```bash
    poetry --version
    ```

### Installation
1. Clone the repository and navigate to the project root
```bash
https://github.com/SBroaddus220/cse5914_capstone_project
cd cse5914_capstone_project
```

2. Install project dependencies
Run the following command to install dependencies via Poetry:
```bash
poetry install
```

3. [Optional] Activate the Poetry Shell (to avoid having to specifically reference the virtual environment)
```bash
poetry shell
```

## Running the Application
To run the application, simply run:
```bash
python ./main.py  # Poetry shell activated
poetry run python ./main.py  # Poetry shell not activated
```

## Authors and Acknowledgement
Steven Broaddus (https://stevenbroaddus.com/#contact)
Guilherme Oliveira (https://github.com/gui2678)
Spencer Hurt (https://github.com/spencer-hurt)
Jerrin Wofford (https://github.com/jerrinw1110)
Scott Caley (https://github.com/scottcaley)
Grant McGeehen (https://github.com/gmcgeehen)

## Contributing
Due to this being a course project, no contributions are allowed probably.

## Natural Language Processing
User enter the natural language to the bar and will be recognized and 
then parse to the function called "process_natural_language" in controller.py
when pressing the 'process' button. 

And then this function will call another function called "get_tags_from_tags"
in tag_generator.py, which invokes the deepseek_chat model to generate the 
tags. There will be 3 tags generated: 1 most relevant combination of what the 
user ask and 2 other related tags(words may not appear in the prompt). And then,
it returns a list of three tags. The tags will be shown in the window.

## PYTHON DOTENV
We hide our sensitive parameters like our api keys in the ".env" file and we load these
parameters in config.py file. When we need to use these parameters, we use
"parameter = os.getenv("PARAMETER")" to get the value.