from setuptools import setup
from pathlib import Path

setup(
    name="Axe",
    version='0.0.5',
    author="Ju Lin",
    author_email="soasme@gmail.com",
    description="Axe is a Python Generative AI toolkit",
    long_description=(Path(__file__).parent / "README.md").read_text(),
    long_description_content_type="text/markdown",
    license="MIT License",
    keywords="AI,GPT,GenerativeAI,Transformer",
    url="https://github.com/soasme/axe",
    packages=['axe'],
    classifiers=[
        "Development Status :: 4 - Beta",
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        "License :: OSI Approved :: MIT License",
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
