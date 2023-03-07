from flask import Flask, render_template, request, g, redirect, url_for, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random
import string
from urllib.parse import urlparse
app = Flask(__name__)

def open_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect("test.db")
        db.row_factory = sqlite3.Row
    return db

def query_db(query, args=()):
    '''
    Returns a list of dicts of column name to value
    '''
    db = open_db()
    cur = db.cursor()
    # Turn on foreign key support as per https://sqlite.org/foreignkeys.html
    cur.execute("PRAGMA foreign_keys=ON")
    cur.execute(query, args)
    id = cur.lastrowid
    rv = cur.fetchall()
    cur.close()
    return rv,id

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.commit()
        db.close()

def insert_room_in_db(roomTitle, roomFloor_Name, roomPassword, labelToLinks, slug):
    password_hash =generate_password_hash(roomPassword)
    insertRoomQuery = '''
    INSERT INTO Rooms(title, floor_name, slug, password_hash)
    VALUES (:title, :floor_name, :slug, :password_hash);
    '''
    
    _, room_id = query_db(insertRoomQuery,
                     {"title":roomTitle, "floor_name":roomFloor_Name,
                      "slug":slug, "password_hash": password_hash})    

    insertLinkQuery = '''
    INSERT INTO Links (url, domainName, description, label, room_id)
    VALUES (:url, :domainName, :description, :label, :room_id);
    '''
    for label, links in labelToLinks.items():
        for link in links:
            domainName = urlparse(link['url']).netloc
            query_db(insertLinkQuery,
                     {'url':link['url'], 'domainName':domainName, 'description':link['description'],
                      'label':label,'room_id':room_id})

def update_room_in_db(changedRoomInfo, addedLinks, removedLinks, roomId):

    updateTitleQuery = '''
    UPDATE Rooms
    SET title = :value
    WHERE id = :room_id
    '''
    updateFloorNameQuery = '''
    UPDATE Rooms
    SET floor_name  = :value
    WHERE id = :room_id
    '''
    updatePasswordQuery = '''
    UPDATE Rooms
    SET password_hash = :value
    WHERE id = :room_id
    '''
    if 'title' in changedRoomInfo:
        query_db(updateTitleQuery, {'value':changedRoomInfo['title'], 'room_id':roomId})
    if 'floor_name' in changedRoomInfo:
        query_db(updateFloorNameQuery, {'value':changedRoomInfo['floor_name'], 'room_id':roomId})
    if 'password' in changedRoomInfo:
        query_db(updatePasswordQuery,{'value':generate_password_hash(changedRoomInfo['password']),'room_id':roomId})
       

    deleteLinkQuery = '''
    DELETE FROM Links
    WHERE url = :url
    AND room_id = :room_id;
    
    '''
    for link in removedLinks:
        query_db(deleteLinkQuery, {'url':link['url'], 'room_id':roomId})

        
    insertLinkQuery = '''
    INSERT INTO Links (url, domainName, description, label, room_id)
    VALUES (:url, :domainName, :description, :label, :room_id);
    '''
    for link in addedLinks:
        #insert links
        domainName = urlparse(link['url']).netloc
        query_db(insertLinkQuery,
                     {'url':link['url'], 'domainName':domainName, 'description':link['description'],
                      'label':link['label'],'room_id':roomId})

def delete_room(room_id):
    deleteLinksQuery = '''
    DELETE FROM Links
    WHERE room_id = :room_id;
    '''
    query_db(deleteLinksQuery, {'room_id':room_id})

    deleteRoomQuery = '''
    DELETE FROM Rooms
    WHERE id = :room_id;
    '''
    query_db(deleteRoomQuery, {'room_id':room_id})

def create_room_slug():
    getSlugsQuery = '''
    SELECT slug FROM Rooms;
    '''
    results,_ = query_db(getSlugsQuery)
    slugs = [result['slug'] for result in results]
    print(slugs)
    newSlug = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
    if newSlug in slugs:
        #Should basically never get here!
        while newSlug in slugs:
            newSlug = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
    return newSlug

def verify_floor_name(floor_name, password):
    getGroupIdQuery = '''
    SELECT * FROM Rooms
    WHERE floor_name = :floor_name;
    '''
    results,_ = query_db(getGroupIdQuery, {'floor_name':floor_name})
    if not results:
        return True
    password_hash = results[0]['password_hash']
    return check_password_hash(password_hash, password)

def get_room_by_slug(slug):
    getRoomQuery = '''
    SELECT * FROM Rooms
    WHERE slug = :slug;
    '''
    rooms,_ = query_db(getRoomQuery, {"slug":slug})
    if not rooms:
        return {}
    #assert len(rooms) == 1
    return rooms[0]

def get_links_for_room(roomId):
    getLinksQuery = '''
    SELECT * FROM Links
    WHERE room_id = :roomId;
    '''
    links,_ = query_db(getLinksQuery, {"roomId":roomId})
    return links

def get_rooms_by_floor_name(floor_name):
    getRoomsQuery = '''
    SELECT * FROM Rooms
    WHERE floor_name = :floor_name
    '''
    return query_db(getRoomsQuery, {'floor_name':floor_name})[0]

def get_random_floors(num, domain):
    if domain:
        getFloorsQuery = '''
        SELECT DISTINCT floor_name FROM Rooms
        WHERE id IN
        (SELECT room_id FROM Links WHERE domainName = :domain)
        ORDER BY RANDOM()
        LIMIT :num
        '''
        floors,_ = query_db(getFloorsQuery, {'num':num, 'domain':domain})
        return [floor['floor_name'] for floor in floors]
    else:
        getFloorsQuery = '''
        SELECT DISTINCT floor_name FROM Rooms
        ORDER BY RANDOM()
        LIMIT :num
        '''
        floors,_ = query_db(getFloorsQuery, {'num':num})
        return [floor['floor_name'] for floor in floors]

def get_random_rooms(num, domain):
    if domain:
        getRoomsQuery = '''
        SELECT * FROM Rooms
        WHERE id IN
        (SELECT room_id FROM Links WHERE domainName = :domain)
        ORDER BY RANDOM()
        LIMIT :num
        '''
        rooms,_ = query_db(getRoomsQuery, {'num':num, 'domain':domain})
        return rooms
    else:
        getRoomsQuery = '''
        SELECT * FROM Rooms
        ORDER BY RANDOM()
        LIMIT :num
        '''
        rooms,_ = query_db(getRoomsQuery, {'num':num})
        return rooms

def get_random_links(num, domain):
    if domain:
        getLinksQuery = '''
        SELECT * FROM Links
        WHERE domainName = :domain
        ORDER BY RANDOM()
        LIMIT :num;
        '''
        links,_ = query_db(getLinksQuery, {'domain':domain, 'num':num})
        return links
    else:
        getLinksQuery = '''
        SELECT * FROM Links
        ORDER BY RANDOM()
        LIMIT :num;
        '''
        links,_ = query_db(getLinksQuery, {'num':num})
        return links

def get_doors_for_room(slug):
    getLinksQuery = '''
    SELECT * FROM Links
    WHERE url = :url;
    '''
    url = 'http://127.0.0.1:5000/room/{}'.format(slug)
    links,_ = query_db(getLinksQuery, {'url':url})
    room_ids = [link['room_id'] for link in links]

    getRoomQuery = '''
    SELECT * FROM Rooms
    WHERE id = :id;
    '''
    doors = []
    for id in room_ids:
        rooms,_ = query_db(getRoomQuery, {'id':id})
        if not rooms:
            pass
        else:
            #assert len(rooms) == 1
            if rooms[0]['slug'] != slug:
                doors.append(rooms[0])
    return doors

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/help', methods=['GET'])
def help():
    return render_template('help.html')

@app.route('/source', methods=['GET'])
def source():
    return send_from_directory('','linktower.html')

@app.route('/new', methods=['GET'])
def get_new_form():
    return render_template("new.html", title='', links='', floor_name='', password='', errors=[])

@app.route('/new', methods=['POST'])
def post_new_form():
    errors = check_form_validity(request)
    form = request.form
    roomSlug = create_room_slug()
    links, badLinks = parse_links_form(request.form['links'])
    labelToLinks = associate_label_to_links(links)
    if badLinks or  errors:
        return render_template("new.html", title=form['title'], links=form['links'],
                               floor_name=form['floor_name'], password=form['password'], errors=badLinks+errors)
    insert_room_in_db(form['title'], form['floor_name'], form['password'], labelToLinks, roomSlug)
    return redirect(url_for('view_room', slug=roomSlug))

@app.route('/room/<slug>', methods=['GET'])
def view_room(slug):
    room = get_room_by_slug(slug)
    if not room:
        return render_template("not_found.html", msg='room at {}'.format(slug))
    links = get_links_for_room(room['id'])
    labelToLinks = associate_label_to_links(links)
    doors = get_doors_for_room(slug)
    return render_template("room.html", room=room, labelToLinks=labelToLinks, doors=doors)

@app.route('/room/<slug>/edit', methods=['GET'])
def get_edit_form(slug):
    room = get_room_by_slug(slug)
    if not room:
        return render_template("not_found.html", msg='room at {}'.format(slug))
    links = get_links_for_room(room['id'])
    labelToLinks = associate_label_to_links(links)
    linksform = []
    for label, linkslist in labelToLinks.items():
        linksform.append(label)
        for link in linkslist:
            linksform.append("[{}]({})".format(link['description'], link['url']))
        linksform.append('\n')
    return render_template("edit.html", title=room['title'], links='\n'.join(linksform),
                               floor_name=room['floor_name'], password='', errors=[])

@app.route('/room/<slug>/edit', methods=['POST'])
def post_edit_form(slug):

    #get room data
    room = get_room_by_slug(slug)
    if not room:
        return render_template("not_found.html", msg='room at {}'.format(slug))

    #get form data
    errors = check_form_validity(request)
    form = request.form
    links, badLinks = parse_links_form(request.form['links'])
    if badLinks or errors:
        return render_template("edit.html", title=form['title'], links=form['links'],
                               floor_name=form['floor_name'], password=form['password'], errors=badLinks+errors)
    
    #normalize links to common format (list of dicts)
    newLinks = set([(link['url'], link['label'], link['description'])
                    for link in links])
    oldLinks = set([(link['url'], link['label'], link['description'])
                    for link in get_links_for_room(room['id'])])
    #diff links
    addedLinks = [{'url':link[0], 'label':link[1], 'description':link[2]} for link in list(newLinks - oldLinks)]
    removedLinks = [{'url':link[0], 'label':link[1], 'description':link[2]} for link in list(oldLinks - newLinks)]
    
    
    changedRoomInfo = {}
    if form['title'] != room['title']:
        changedRoomInfo['title'] = form['title']
    if form['floor_name'] != room['floor_name']:
        changedRoomInfo['floor'] = form['floor']
    if form['new_password']:
        changedRoomInfo['password'] = form['new_password']
        

    
    update_room_in_db(changedRoomInfo, addedLinks, removedLinks, room['id'])
    return redirect(url_for('view_room', slug=slug))

@app.route('/room/<slug>/delete', methods=['GET'])
def get_delete_room_form(slug):
    room = get_room_by_slug(slug)
    if not room:
        return render_template("not_found.html", msg='room at {}'.format(slug))
    return render_template("delete.html", room=room, errors=[], success=False)

@app.route('/room/<slug>/delete', methods=['POST'])
def post_delete_room_form(slug):
    room = get_room_by_slug(slug)
    password = request.form['password']
    if not room:
        return render_template("not_found.html", msg='room at {}'.format(slug))
    if not check_password_hash(room['password_hash'], password):
        return render_template("delete.html", room=room, errors=['Incorrect password'], success=False)
    delete_room(room['id'])
    return render_template("delete.html", room=room, errors=[], success=True)

@app.route('/floor/<floor_name>', methods=['GET'])
def list_rooms_on_floor(floor_name):
    rooms = get_rooms_by_floor_name(floor_name)
    if not rooms:
       return  render_template("not_found.html", msg='floor with name {}'.format(floor_name))
    return render_template("floor_name.html", floor_name=floor_name, rooms=rooms)

@app.route('/discover', methods=['GET'])
def discover_get():
    floors = get_random_floors(10, '')
    rooms = get_random_rooms(10, '')
    links = get_random_links(10, '')    
    return render_template('discover.html', num=10, floors=floors, rooms=rooms, links=links)

@app.route('/discover', methods=['POST'])
def discover_post():
    form = request.form
    floors = get_random_floors(10, form['domain'])
    rooms = get_random_rooms(10, form['domain'])
    links = get_random_links(10, form['domain'])
    return render_template('discover.html', num=10, floors=floors, rooms=rooms, links=links)

def parse_links_form(form):
    links = []
    currentLabel = ''
    badInput = []
    existingUrls = set()
    for line in form.splitlines():
        if line.endswith(':'):
            currentLabel = line
        elif len(set(line) - set(string.whitespace)) == 0:
            pass
        #parse the markdown link for its components 
        elif line.startswith('[') and '](' in line and line.endswith(')'):
            description = line[1:line.index('](')]
            url = line[line.index('](')+2:-1]
            parsedUrl = urlparse(url)
            
            #check if url is valid
            if not all([parsedUrl.scheme, parsedUrl.netloc, parsedUrl.path]):
                badInput.append(line + " Could not parse link. Try copying the link from your browser's search bar")
            elif url in existingUrls:
                badInput.append(line + " Duplicate urls are not accepted. Delete this line and resubmit the form")
            else:
                links.append({'description':description, 'url':url, 'label':currentLabel})
                existingUrls.add(url)
            
        else:
            badInput.append(line + " This line is not recognized as a link or label")

    return (links, badInput)

def associate_label_to_links(links):
    labelToLinks = {}
    for link in links:
        label = link['label']
        labelToLinks.setdefault(label, []).append(link)
    return {i[0]:i[1] for i in sorted(labelToLinks.items())}

def check_form_validity(requests):
    roomTitle = request.form['title']
    roomFloor_Name = request.form['floor_name']
    roomPassword = request.form['password']
    roomLinks = request.form['links']
    
    #check for empty fields
    
    errors = []
    
    if not roomTitle:
        errors.append('Title field is empty')
    if not roomFloor_Name:
        errors.append('Floor Name field is empty')
    if not roomPassword:
        errors.append('Password field is empty')
    if not roomLinks:
        errors.append('Title field is empty')
        
    illegalChars = set(roomFloor_Name) - set(string.ascii_letters + string.digits)
    if illegalChars:
        errors.append('Floor name must be ascii letters and numbers only, {} not allowed'.format(illegalChars))
    if not verify_floor_name(roomFloor_Name, roomPassword):
        errors.append('Incorrect password for floor {}'.format(roomFloor_Name))
    return errors
