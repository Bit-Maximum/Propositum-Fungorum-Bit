from pathlib import Path


class PromptManager:
    def __init__(self, path: Path) -> None:
        self.path_to_prompts: Path = path
        self.step_to_file_mapper: dict[int, Path] = self.__get_files_dict(path)

    def get_step_prompt(self, step_number: int) -> Path | None:
        return self.step_to_file_mapper.get(step_number, None)

    def __get_files_dict(self, path: Path) -> dict[int, Path]:
        files: list[str] = sorted(
            (item
            for item in path.iterdir()
            if item.is_file() and not item.name.startswith('.')),
            key=lambda item: item.name
        )

        return {
            index: filename
            for index, filename in enumerate(files, start=1)
        }


if __name__ == '__main__':
    mng = PromptManager(Path("/Users/artemsulatev/Desktop/Gribova/gribova/llm-parser/app/pipeline/prompts"))
    print(mng.step_to_file_mapper)
