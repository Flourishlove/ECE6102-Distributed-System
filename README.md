ECE6102 course assignment
Click to View [Music-Repository](http://xingyu-liu-music-shopping.appspot.com/)

# Music Repository

Music repository is a place where user can save and query songs' info. There are total three basic genres: hip-hop, classical and jazz. Maintain a shopping cart and allow customers to add songs they browse or search for to the shopping cart.

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


## Products
- [App Engine][1]

## Language
- [Python][2]

## APIs
- [NDB Datastore API][3]
- [Users API][4]

## Dependencies
- [webapp2][5]
- [jinja2][6]
- [Twitter Bootstrap][7]