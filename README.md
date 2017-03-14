ECE6102 course assignment
URL: http://xingyu-liu-music-shopping.appspot.com/

# Music Repository

Music repository is a place where user can save and query songs' info. There are total three basic genres: hip-hop, classical and jazz.

Basic Requirement:
1. Error handling for inputs: Check for empty inputs (either the artist field or the title field or both when entering a song and the artist field when searching for a song) and display an appropriate error message when an input field is left empty.
2. Case sensitivity: Genre names and search strings should not be case sensitive. So, if you enter "Classical" or "classical" as the genre, these should direct to the same set of entries in the data store. Similarly, "dav" or "Dav" should match "Miles Davis" in the author search feature.
3. Returning to main page: There should be a simple way for users to return to the main page of your repository (the one titled "Doug Blough's eTunes Repository" in the Python example application) without having to use the back button. This can be easily handled by including a clickable link that takes the browser back to the main page on every other page of the repository.
4. Failed searches: If a search string is entered that does not match any artists in the data store entries, an appropriate message should be displayed (instead of just redisplaying the search page without any results).


Besides, maintain a shopping cart and allow customers to add songs they browse or search for to the shopping cart.

Shopping Cart Requirement:
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