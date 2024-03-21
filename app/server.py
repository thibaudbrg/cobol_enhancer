from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langserve import add_routes
#from cobol_enhancer import chain as ubp_cobol_chain

app = FastAPI()


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


# Edit this to add the chain you want to add
#add_routes(app, ubp_cobol_chain, path="/", playground_type="chat")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
