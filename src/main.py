import argparse

from pydantic import BaseModel

from bq_table_reference.application.dataset_loader import DatasetLoader


class Args(BaseModel):
    project: str


def main():
    parser = argparse.ArgumentParser(prog="bigquery-dashboard")
    parser.add_argument("--project", type=str, required=True)
    args = parser.parse_args()

    _args = Args.model_validate(args.__dict__)

    dataset_loader = DatasetLoader(project=_args.project)
    result = dataset_loader.load_all(project=_args.project)
    print(result)


if __name__ == "__main__":
    main()
