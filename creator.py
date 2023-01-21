from jinja2 import Template, Environment, FileSystemLoader
import pandas as pd
import uuid
import re
from datetime import datetime
import hashlib
from js import document, console
import asyncio
import js
from pyodide import create_proxy
import io
from js import document, console, Uint8Array, window, File
from os import listdir, getcwd, mkdir, rmdir
from os.path import isfile, join, exists


context = {"now": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}


# Custom filter method
def regex_replace(s, find, replace):
    """A non-optimal implementation of a regex filter"""
    return re.sub(find, replace, s)


# DATA_FILE = sys.argv[1]
TEMPLATE_FOLDER = "templates/"
# OUTPUT_FOLDER = sys.argv[3]

env = Environment(loader=FileSystemLoader(TEMPLATE_FOLDER), trim_blocks=True)
env.filters["regex_replace"] = regex_replace


def hash_id(string):
    hash_object = hashlib.md5(bytes(string, "utf-8"))
    return str(hash_object.hexdigest())


env.filters["create_hash_id"] = hash_id


def create_from_template(DATA_FILE):
    elements = [
        "AdministrableProductDefinition",
        "Substance",
        "RegulatedAuthorization",
        "Organization",
        "ClinicalUseDefinition",
        "Composition",
        "Ingredient",
        "MedicinalProductDefinition",
        "ManufacturedItemDefinition",
        "PackagedProductDefinition",
        "Bundle",
    ]
    fileList = document.getElementById("input").files
    TEMPLATE_FOLDER = "templates/"
    # OUTPUT_FOLDER = "output/"
    # create temp_folder:
    # print(DATA_FILE, TEMPLATE_FOLDER, OUTPUT_FOLDER)
    print(DATA_FILE)

    # print(getcwd())
    temp_folder = getcwd() + "/temp/"

    if not exists(temp_folder):
        mkdir(temp_folder)
    major_name = (
        "acme"  # DATA_FILE.lower().split("/")[-1].split(".")[0].replace(" ", "_")
    )
    real_output_folder = getcwd() + "output/"

    if not exists(real_output_folder):
        mkdir(real_output_folder)
    for sheet in elements:
        # read an excel file and convert
        # into a dataframe object
        df = pd.DataFrame(pd.read_excel(DATA_FILE, sheet_name=sheet))
        #   pre_validation(df, sheet)
        df["id_hash"] = df["id"].apply(lambda x: uuid.uuid4())
        df["id"].fillna(df["id_hash"], inplace=True)
        # show the dataframe
        #   print(df)
        df.to_csv(temp_folder + sheet + ".csv", index=True)

    data_dict = {"MajorName": major_name}  # if needed
    data = {"dictionary": data_dict, "turn": "1"}

    # multiple elementsa
    for file in listdir(temp_folder):
        print(file)
        n_file = file.split(".")[0]
        # with open(TEMPLATE_FOLDER + n_file + ".fsh", "r") as file:

        # templateString = env.get_template(file.read())

        t = env.get_template(n_file + ".fsh")
        # t = Template(templateString, trim_blocks=True)

        df = pd.read_csv(temp_folder + n_file + ".csv", index_col=0)

        df = df.astype(str)
        data["data"] = df
        t.stream(data=data, **context).dump(real_output_folder + n_file + ".fsh")

        # get ids:
        ## goes for all, checks for ID and adds to list
        ## then creates again with references
    object_ids = {}
    for file in listdir(real_output_folder):
        #  print(file)
        # n_file = file.split(".")[0]
        with open(real_output_folder + file, "r") as file1:
            Lines = file1.readlines()
            instances = []
            ids = []
            for line in Lines:

                if "Instance: " in line:
                    # print(line)
                    instances.append(line.replace("Instance: ", "").strip())
                    # if "* id = " in line:
                    # print(line)
                    ids.append(line.replace("Instance: ", "").strip())

            object_ids[file.split(".")[0]] = [(i, j) for i, j in zip(instances, ids)]

    print("ob", object_ids)
    data["references"] = object_ids

    print("newline" + " ---" * 30)
    # multiple elementsa
    for file in listdir(temp_folder):
        # print(file)
        n_file = file.split(".")[0]
        # with open(TEMPLATE_FOLDER + n_file + ".fsh", "r") as f:
        #     templateString = f.read()
        # t = Template(templateString, trim_blocks=True)
        t = env.get_template(n_file + ".fsh")

        df = pd.read_csv(temp_folder + file, index_col=0)
        # print(df)
        df = df.astype(str)
        data["data"] = df
        data["turn"] = "2"
        t.stream(data=data, **context).dump(real_output_folder + n_file + ".fsh")


import asyncio
from js import document, FileReader
from pyodide import create_proxy


async def process_file(event):
    fileList = event.target.files.to_py()

    for f in fileList:
        # data = await f.text()
        array_buf = Uint8Array.new(await f.arrayBuffer())
        bytes_list = bytearray(array_buf)
        data = io.BytesIO(bytes_list)
        create_from_template(data)
        # document.getElementById("input").innerHTML = data


def main():
    # Create a Python proxy for the callback function
    # process_file() is your function to process events from FileReader
    file_event = create_proxy(process_file)

    # Set the listener to the callback
    e = document.getElementById("input")
    e.addEventListener("change", file_event, False)


main()


async def _upload_change_and_show(e):
    # Get the first file from upload
    file_list = e.target.files
    first_item = file_list.item(0)

    # Get the data from the files arrayBuffer as an array of unsigned bytes
    array_buf = Uint8Array.new(await first_item.arrayBuffer())

    # BytesIO wants a bytes-like object, so convert to bytearray first
    bytes_list = bytearray(array_buf)
    my_bytes = io.BytesIO(bytes_list)

    # Create PIL image from np array
    my_image = Image.open(my_bytes)

    # Log some of the image data for testing
    console.log(f"{my_image.format= } {my_image.width= } {my_image.height= }")

    # Now that we have the image loaded with PIL, we can use all the tools it makes available.
    # "Emboss" the image, rotate 45 degrees, fill with dark green
    my_image = (
        my_image.filter(ImageFilter.EMBOSS)
        .rotate(45, expand=True, fillcolor=(0, 100, 50))
        .resize((300, 300))
    )

    # Convert Pillow object array back into File type that createObjectURL will take
    my_stream = io.BytesIO()
    my_image.save(my_stream, format="PNG")

    # Create a JS File object with our data and the proper mime type
    image_file = File.new(
        [Uint8Array.new(my_stream.getvalue())],
        "new_image_file.png",
        {type: "image/png"},
    )

    # Create new tag and insert into page
    new_image = document.createElement("img")
    new_image.src = window.URL.createObjectURL(image_file)
    document.getElementById("output_upload_pillow").appendChild(new_image)
