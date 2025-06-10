from random import randrange
import time
from typing import Optional
from fastapi import FastAPI, Response, status, HTTPException, Depends
from fastapi.params import Body
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy.orm import Session

from . import models
from .database import engine, get_db  # Import the database engine from the database module

# This is for the ORM SQLAlchemy, but we are not using it in this example
models.Base.metadata.create_all(bind=engine)  # Create the database tables if they don't exist


        
app = FastAPI()

# Define a Pydantic model for the post data so that FastAPI can validate the request body
class Post(BaseModel):
    title: str
    content: str
    published: bool = False  # Default value for published is True
    rating: Optional[int] = None  # Optional field with no default value

while True:
    try:
        conn = psycopg2.connect(host="localhost", database="fastapi", user="postgres", password="supersecretpassword", cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print("Connected to the database successfully")
        break
    except Exception as e:
        print(f"Failed to connect to the database: {e}")
        time.sleep(2)  # Wait for 2 seconds before retrying

@app.get("/")
async def root():
    return {"message": "Hello World Bitch"}

############## All the session related endpoints are collected here. THEY WILL NOT USE THE DATABASE

# Initialize an empty list to store posts in SESSION memory
my_posts = []  # This will hold the posts in memory; 

# For Debugging purpose
my_posts = [{"title": "Post 1", "content": "Content of post 1", "published": True, "rating": 5, "id": 1},
            {"title": "Post 2", "content": "Content of post 2", "published": False, "rating": 3, "id": 2}]

def find_post(id: int):
    # Helper function to find a post by ID
    return next((post for post in my_posts if post['id'] == id), None)

def find_post_index(id: int):
    # Helper function to find the index of a post by ID
    return next((index for index, post in enumerate(my_posts) if post['id'] == id), None)


@app.get("/session/posts")
def get_posts():
    return {"data": my_posts}


@app.post("/session/posts", status_code=status.HTTP_201_CREATED)
def create_posts(post: Post):
    # Convert the Pydantic model to a dictionary and add it to the list of posts
    new_post = post.model_dump()  # Convert the Pydantic model to a dictionary
    new_post['id'] = randrange(1, 1000000)  # Generate a random ID for the post
    # Add the post to the list of posts
    print(new_post)
    my_posts.append(new_post)  # Append the new post to the list
    return {"new_post": f"title {new_post['title']} and content {new_post['content']}"} #f String allows you to use variables inside a string
    

# IMPORTANT ORDER: This has to be before get id posts because otherwise /post/{id} will match /posts/latest which is not what we want
@app.get("/session/posts/latest", status_code=status.HTTP_200_OK)
def get_latest_post(response: Response):
    # If there are no posts, return a 404 Not Found response
    if not my_posts:
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No posts available")
    
    # Return the latest post (the last one in the list)
    latest_post = my_posts[-1]
    return {"data": latest_post}

@app.get("/session/posts/{id}", status_code=status.HTTP_200_OK)
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
    
@app.delete("/session/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, response: Response):
    # Find the post with the given ID
    post = find_post(id)

    if post:
        my_posts.remove(post)   # Remove the post from the list
        # ALTERNATIVE: my_posts.pop(find_post_index(id))  # Remove the post by index as shown in KodeKloud
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} was not found")
    

@app.put("/session/posts/{id}", status_code=status.HTTP_200_OK)
def update_post(id: int, post: Post, response: Response):
    # Find the post with the given ID
    post_index = find_post_index(id)

    # If the post is found, update it; otherwise, return a 404 Not Found response
    if post is not None:
        updated_post = post.model_dump()    # Convert the Pydantic model to a dictionary
        updated_post['id'] = id
        my_posts[post_index] = updated_post  # Update the post in the list
        return {"data": post}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} was not found")
       

##################################### All the database related endpoints are collected here. THEY WILL USE THE DATABASE


@app.get("/posts/sqlaclchemy")
def get_posts_sqlalchemy(db: Session = Depends(get_db)):
    # Fetch all posts from the database using SQLAlchemy
    return {'status': 'success'}


@app.get("/posts")
def get_posts():
    cursor.execute("""SELECT * FROM posts""")
    my_posts = cursor.fetchall()  # Fetch all posts from the database
    # If there are no posts, return an empty list
    return {"data": my_posts}



@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_posts(post: Post):
    # Insert the new post into the database
    cursor.execute(
        """INSERT INTO posts (title, content, published, rating) VALUES (%s, %s, %s, %s) RETURNING *""",
        (post.title, post.content, post.published, post.rating)
    )
    new_post = cursor.fetchone()  # Fetch the newly created post from the database
    conn.commit()  # Commit the transaction to save changes to the database
    return {"data": new_post}  # Return the list of posts with a 201 Created status code

# IMPORTANT ORDER: This has to be before get id posts because otherwise /post/{id} will match /posts/latest which is not what we want
@app.get("/posts/latest", status_code=status.HTTP_200_OK)
def get_latest_post(response: Response):
    # If there are no posts, return a 404 Not Found response
    if not my_posts:
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No posts available")
    
    cursor.execute("""SELECT * FROM posts order by created_at DESC LIMIT 1;""")  # Fetch the latest post from the database

    latest_post = cursor.fetchall()  # Fetch the post with the given ID from the database
    return {"data": latest_post}

@app.get("/posts/{id}", status_code=status.HTTP_200_OK)
def get_post(id: int, response: Response):
    cursor.execute("""SELECT * FROM posts WHERE id = %s""", (str(id)))
    post = cursor.fetchone()  # Fetch the post with the given ID from the database
    # If the post is found, return it; otherwise, return a 404 Not Found response
    if post:
        return {"data": post}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} was not found")

    
@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, response: Response):
    # Find the post with the given ID
    cursor.execute("""DELETE FROM posts WHERE id = %s RETURNING *""", (str(id),))
    post = cursor.fetchone()  # Fetch the post with the given ID from the database
    conn.commit()

    if post:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} was not found")
    

@app.put("/posts/{id}", status_code=status.HTTP_200_OK)
def update_post(id: int, post: Post, response: Response):
    # Find the post with the given ID
    cursor.execute("""UPDATE posts SET title = %s, content = %s, published = %s, rating = %s WHERE id = %s RETURNING *""",
                   (post.title, post.content, post.published, post.rating, str(id)))
    post = cursor.fetchone()
    conn.commit()
    # If the post is found, update it; otherwise, return a 404 Not Found response
    if post is not None:
        return {"data": post}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} was not found")
       