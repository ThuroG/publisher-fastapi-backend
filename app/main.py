from random import randrange
import time
from typing import Optional
from fastapi import FastAPI, Response, status, HTTPException
from fastapi.params import Body
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor



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

# Initialize an empty list to store posts
my_posts = []  # This will hold the posts in memory; 

# For Debugging purpose
#my_posts = [{"title": "Post 1", "content": "Content of post 1", "published": True, "rating": 5, "id": 1},
 #          {"title": "Post 2", "content": "Content of post 2", "published": False, "rating": 3, "id": 2}]

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
    cursor.execute("""SELECT * FROM posts""")
    my_posts = cursor.fetchall()  # Fetch all posts from the database
    # If there are no posts, return an empty list
    return {"data": my_posts}

@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_posts(post: Post):
    # NOTNEEDEDANYMORE: post_dict['id'] = randrange(1, 1000000)  # Generate a random ID for the post
    # Insert the new post into the database
    cursor.execute(
        """INSERT INTO posts (title, content, published, rating) VALUES (%s, %s, %s, %s) RETURNING *""",
        (post.title, post.content, post.published, post.rating)
    )
    new_post = cursor.fetchone()  # Fetch the newly created post from the database
    # Add the new post to the list of posts
    my_posts.append(post)
    # Here you would typically save the post to a database
    # return {"new_post": f"title {new_post['title']} and content {new_post['content']}"} #f String allows you to use variables inside a string
    
    conn.commit()  # Commit the transaction to save changes to the database
    return {"data": new_post}  # Return the list of posts with a 201 Created status code

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
    # NOT USED ANYMORE latest_post = my_posts[-1]
    cursor.execute("""SELECT * FROM posts order by created_at DESC LIMIT 1;""")  # Fetch the latest post from the database
    # The DISTINCT ON clause is used to get the latest post based on the created_at timestamp
    latest_post = cursor.fetchall()  # Fetch the post with the given ID from the database
    return {"data": latest_post}

@app.get("/posts/{id}", status_code=status.HTTP_200_OK)
def get_post(id: int, response: Response):
    cursor.execute("""SELECT * FROM posts WHERE id = %s""", (str(id)))
    post = cursor.fetchone()  # Fetch the post with the given ID from the database
    # Find the post with the given ID
    # NOTUSEDANYMORE post = find_post(id)
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
    # NOT USED ANYMORE post = find_post(id)
    # If the post is found, delete it; otherwise, return a 404 Not Found response
    cursor.execute("""DELETE FROM posts WHERE id = %s RETURNING *""", (str(id),))
    post = cursor.fetchone()  # Fetch the post with the given ID from the database
    conn.commit()

    if post:
        # NOT NEEDED ANYMORE my_posts.remove(post)   # Remove the post from the list
        # ALTERNATIVE: my_posts.pop(find_post_index(id))  # Remove the post by index as shown in KodeKloud
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} was not found")
    

@app.put("/posts/{id}", status_code=status.HTTP_200_OK)
def update_post(id: int, post: Post, response: Response):
    # Find the post with the given ID
    # NOT NEEDED ANYMORE post_index = find_post_index(id)

    cursor.execute("""UPDATE posts SET title = %s, content = %s, published = %s, rating = %s WHERE id = %s RETURNING *""",
                   (post.title, post.content, post.published, post.rating, str(id)))
    post = cursor.fetchone()
    conn.commit()
    # If the post is found, update it; otherwise, return a 404 Not Found response
    if post is not None:
       # updated_post = post.model_dump()    # Convert the Pydantic model to a dictionary
       # updated_post['id'] = id
       # my_posts[post_index] = updated_post  # Update the post in the list
        return {"data": post}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} was not found")
       