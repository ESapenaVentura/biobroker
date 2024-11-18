import os

def remove_generated_files(paths: list):
    for file in paths:
        os.remove(file)


def before_feature(context, feature):
    if "integration" in feature.tags:
        feature.skip("Integration tests have to be triggered explicitly")
        return


def after_scenario(context, scenario):
    match scenario.name:
        case x if x.startswith("Save metadata to source --"):
            remove_generated_files([context.output_file_path])

