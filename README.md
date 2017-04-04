ECE6102 course assignment

Click to View [Music-Repository](http://xingyu-liu-music-shopping.appspot.com/) 

Click to View [Transactions-Mapreduce-Analysis](http://music-mapreduce-xingyu-liu.appspot.com/)

# Music Repository

Music repository is a place where user can save and query songs' info. There are total three basic genres: hip-hop, classical and jazz. Maintain a shopping cart and allow customers to add songs they browse or search for to the shopping cart. Design Mapreduce algorithm to analyze purchasing data generated from music shopping app using Google mapreduce opensource module.

## Basic Requirement
1. Error handling for inputs: Check for empty inputs and display an appropriate error message when an input field is left empty.
2. Case sensitivity: Genre names and search strings should not be case sensitive.
3. Returning to main page: There should be a simple way for users to return to the main page of your repository without having to use the back button.
4. Failed searches: If a search string is entered that does not match any artists in the data store entries, an appropriate message should be displayed.

## Shopping Cart Requirement:
1. The browse and search displays must also include a mechanism for users to add any displayed song to their shopping cart.
2. There must be a way for users to display the items currently in the shopping cart along with the total cost of the items, and a way to delete items from the cart.
3. The shopping cart key should be unique to a specific user so that multiple users can access the service simultaneously and maintain their own shopping carts.
4. There should be a purchase feature, which allows users to buy the items in the cart. This should clear out the shopping cart and display a message thanking the user for their purchase. This action should also write entries to the data store to record the songs purchased and their prices, the date and time, and the user ID of the purchaser.

## Mapreduce Requirement:
A purchase includes date and time, user ID, song title, artist name, album title, genre, song running time, and price.
Design Mapreduce code to implement the following analyses
1. Count the number of songs sold for each song that has been purchased at least once.
2. Calculate the total dollar amount of sales for each song.
3. Count the number of songs sold for each artist that has had at least one.
4. Calculate the total dollar amount of sales for each artist.
5. For each song that was purchased at least once, find the other song that was purchased most often at the same time and count how many times the two songs were purchased together.

## Products
- [App Engine]

## Language
- [Python]

## APIs
- [NDB Datastore API]
- [Users API]

## Dependencies
- [webapp2]
- [jinja2]
- [Twitter Bootstrap]
