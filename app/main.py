from random import randrange
from typing import Optional
from fastapi import FastAPI, Response, status, HTTPException
from fastapi.params import Body
from pydantic import BaseModel

app = FastAPI()

# Define a Pydantic model for the post data so that FastAPI can validate the request body
class Post(BaseModel):
    title: str
    content: str
    published: bool = True  # Default value for published is True
    rating: Optional[int] = None  # Optional field with no default value

my_posts = [{"title": "Post 1", "content": "Content of post 1", "published": True, "rating": 5, "id": 1},
           {"title": "Post 2", "content": "Content of post 2", "published": False, "rating": 3, "id": 2}]

def find_post(id: int):
    # Helper function to find a post by ID
    return next((post for post in my_posts if post['id'] == id), None)

def find_post_index(id: int):
    # Helper function to find the index of a post by ID
    return next((index for index, post in enumerate(my_posts) if post['id'] == id), None)

@app.get("/")
async def root():
    return {"message": "Hello World Bitch"}

@app.get("/posts")
def get_posts():
    return {"data": my_posts}

@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_posts(post: Post):
    post_dict = post.model_dump()
    post_dict['id'] = randrange(1, 1000000)  # Generate a random ID for the post
    # Add the new post to the list of posts
    my_posts.append(post_dict)
    # Here you would typically save the post to a database
    # return {"new_post": f"title {new_post['title']} and content {new_post['content']}"} #f String allows you to use variables inside a string
    return {"data": my_posts}  # Return the list of posts with a 201 Created status code

# IMPORTANT ORDER: This has to be before get id posts because otherwise /post/{id} will match /posts/latest which is not what we want
@app.get("/posts/latest", status_code=status.HTTP_200_OK)
def get_latest_post(response: Response):
    # If there are no posts, return a 404 Not Found response
    if not my_posts:
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No posts available")
       # Alternatively, you can set the response status code directly
        # response.status_code = status.HTTP_404_NOT_FOUND
        # return {"error": "No posts available"}
    
    # Return the latest post (the last one in the list)
    latest_post = my_posts[-1]
    return {"data": latest_post}

@app.get("/posts/{id}", status_code=status.HTTP_200_OK)
def get_post(id: int, response: Response):
    # Find the post with the given ID
    post = find_post(id)
    # If the post is found, return it; otherwise, return a 404 Not Found response
    if post:
        return {"data": post}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} was not found")
        #response.status_code = status.HTTP_404_NOT_FOUND
        #return {"error": f"Post with id: {id} was not found"}
    
@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, response: Response):
    # Find the post with the given ID
    post = find_post(id)
    # If the post is found, delete it; otherwise, return a 404 Not Found response
    if post:
        my_posts.remove(post)   # Remove the post from the list
        # ALTERNATIVE: my_posts.pop(find_post_index(id))  # Remove the post by index as shown in KodeKloud
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} was not found")
    

@app.put("/posts/{id}", status_code=status.HTTP_200_OK)
def update_post(id: int, post: Post, response: Response):
    # Find the post with the given ID
    post_index = find_post_index(id)
    # If the post is found, update it; otherwise, return a 404 Not Found response
    if post_index is not None:
        updated_post = post.model_dump()    # Convert the Pydantic model to a dictionary
        updated_post['id'] = id
        my_posts[post_index] = updated_post  # Update the post in the list
        return {"data": updated_post}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} was not found")
       