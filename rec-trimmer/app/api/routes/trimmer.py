import logging

from fastapi import (
    APIRouter,
    status,
    UploadFile,
)

import app.file_manager as FM


logger = logging.getLogger(__name__)


router: APIRouter = APIRouter(
    prefix="/trimmer",
    tags=["trimmer",]
)


@router.post(
    path="/",
    status_code=status.HTTP_201_CREATED,
    response_model=FM.models.PipelineResult
)
async def trim(
    file: UploadFile,
) -> FM.models.PipelineResult:
    logger.warning("Считывание файла")

    file_content = await file.read()

    id_generator = FM.id_generator.UUIDGenerator()
    parser = FM.file_parser.PyMuPDFParser()
    analyzer = FM.file_analyzer.BasicFileAnalyzer(
        FM.similarity_calculator.JaccardCalculator()
    )
    repository = FM.file_repository.LocalFileRepository()
    page_resolver = FM.page_range_resolver.MergeResolver()
    page_merge_tool = FM.merge_tool.PyMuPDFMergeTool()

    pipeline = FM.pipeline.TrimmerPipline(
       id_generator=id_generator,
       parser=parser,
       analyzer=analyzer,
       repository=repository,
       page_resolver=page_resolver,
       page_merge_tool=page_merge_tool
    )

    logger.warning("Запуск пайплайна...")

    return await pipeline.run(
        file_content,
        patterns=[
            FM.models.SearchPattern("Хирургическое лечение"),
            FM.models.SearchPattern("Хирургическо-ортопедический способ лечения"),
            FM.models.SearchPattern("Хирургическое лечение для детей и взрослых"),
            FM.models.SearchPattern("Хирургическое лечение детей и взрослых"),
        ]
    )
