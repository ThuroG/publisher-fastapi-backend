from typing import Optional
from fastapi import FastAPI
from fastapi.params import Body
from pydantic import BaseModel

app = FastAPI()

# Define a Pydantic model for the post data so that FastAPI can validate the request body
class Post(BaseModel):
    title: str
    content: str
    published: bool = True  # Default value for published is True
    rating: Optional[int] = None  # Optional field with no default value

@app.get("/")
async def root():
    return {"message": "Hello World Bitch"}

@app.get("/posts")
def get_posts():
    return [
        {"id": 1, "title": "Post 1", "content": "Content of post 1", "published": True},
        {"id": 2, "title": "Post 2", "content": "Content of post 2", "published": False},
    ]

@app.post("/createposts")
def create_post(post: Post):
    print(post)
    # Here you would typically save the post to a database
    # return {"new_post": f"title {new_post['title']} and content {new_post['content']}"} #f String allows you to use variables inside a string
    return {"data": post.model_dump()}

