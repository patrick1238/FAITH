import Source.Objects.Config as Config
import Source.Objects.Database as db

__SCRIPT_NAME="savedict"

def main():
    config = Config.load()
    if config.get("savedict_databasetype") == "case":
        df = db.load().get_database_dataframe()
        for index,group in df.groupby("Diagnosis"):
            print(index,len(group.index))
        df.to_excel(config.get("output")+config.get("runid")+"_cases.xlsx",index=False)
    if config.get("savedict_databasetype") == "cell":
        df = db.load().get_cells_dataframe()
        df.to_excel(config.get("output")+config.get("runid")+"_cells.xlsx",index=False)