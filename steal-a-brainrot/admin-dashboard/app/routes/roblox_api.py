from flask import Blueprint, request, jsonify
import requests as http_requests
from datetime import datetime
from app.models import db, ActivityLog
from app.services.brainrot_catalog import BRAINROT_CATALOG, BRAINROT_SET, match_inventory, get_total_count

roblox_api = Blueprint('roblox_api', __name__)

# --------------------------------------------------------------------------
#  /api/roblox/search-username?username=<name>
#  Queries the public Roblox Users API. No password needed.
# --------------------------------------------------------------------------
@roblox_api.route('/search-username', methods=['GET'])
def search_username():
    username = request.args.get('username', '').strip()
    if not username:
        return jsonify({'success': False, 'message': 'Missing ?username= parameter'}), 400

    try:
        # Roblox public API — usernames to userId
        roblox_resp = http_requests.post(
            'https://users.roblox.com/v1/usernames/users',
            json={
                'usernames': [username],
                'excludeBannedUsers': False
            },
            timeout=8
        )
        roblox_resp.raise_for_status()
        data = roblox_resp.json()

        if not data.get('data'):
            return jsonify({
                'success': False,
                'message': f'No Roblox user found with username "{username}"'
            }), 404

        user_entry = data['data'][0]
        user_id = user_entry['id']

        # Fetch full profile details
        profile_resp = http_requests.get(
            f'https://users.roblox.com/v1/users/{user_id}',
            timeout=8
        )
        profile_resp.raise_for_status()
        profile = profile_resp.json()

        # Fetch avatar thumbnail (headshot 150x150)
        thumb_resp = http_requests.get(
            f'https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=150x150&format=Png&isCircular=false',
            timeout=8
        )
        avatar_url = None
        if thumb_resp.status_code == 200:
            thumb_data = thumb_resp.json()
            if thumb_data.get('data') and len(thumb_data['data']) > 0:
                avatar_url = thumb_data['data'][0].get('imageUrl')

        # Fetch presence (online/offline/in-game)
        presence_resp = http_requests.post(
            'https://presence.roblox.com/v1/presence/users',
            json={'userIds': [user_id]},
            timeout=8
        )
        presence = {}
        if presence_resp.status_code == 200:
            pres_data = presence_resp.json()
            if pres_data.get('userPresences') and len(pres_data['userPresences']) > 0:
                p = pres_data['userPresences'][0]
                status_map = {0: 'Offline', 1: 'Online', 2: 'In-Game', 3: 'In-Studio'}
                presence = {
                    'status': status_map.get(p.get('userPresenceType', 0), 'Unknown'),
                    'last_location': p.get('lastLocation'),
                    'place_id': p.get('placeId'),
                    'game_id': p.get('gameId'),
                    'last_online': p.get('lastOnline')
                }

        result = {
            'success': True,
            'user': {
                'id': profile.get('id'),
                'name': profile.get('name'),
                'display_name': profile.get('displayName'),
                'description': (profile.get('description') or '')[:200],
                'created': profile.get('created'),
                'is_banned': profile.get('isBanned', False),
                'has_verified_badge': profile.get('hasVerifiedBadge', False),
                'avatar_url': avatar_url,
                'profile_url': f"https://www.roblox.com/users/{user_id}/profile"
            },
            'presence': presence,
            'queried_at': datetime.utcnow().isoformat()
        }

        # Log the search event
        log = ActivityLog(
            event_type='ROBLOX_SEARCH',
            ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
            details=f"Searched username: {username} -> userId: {user_id}"
        )
        db.session.add(log)
        db.session.commit()

        return jsonify(result)

    except http_requests.exceptions.Timeout:
        return jsonify({'success': False, 'message': 'Roblox API request timed out. Try again.'}), 504
    except http_requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'message': f'Roblox API error: {str(e)}'}), 502
    except Exception as e:
        return jsonify({'success': False, 'message': f'Internal error: {str(e)}'}), 500


# --------------------------------------------------------------------------
#  /api/roblox/avatar-thumbnail?userId=<id>
#  Proxy route to retrieve avatar headshot to bypass browser CORS block.
# --------------------------------------------------------------------------
@roblox_api.route('/avatar-thumbnail', methods=['GET'])
def get_avatar_thumbnail():
    user_id = request.args.get('userId', '').strip()
    if not user_id:
        return jsonify({'success': False, 'message': 'Missing userId parameter'}), 400

    try:
        thumb_resp = http_requests.get(
            f'https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=100x100&format=Png&isCircular=true',
            timeout=8
        )
        if thumb_resp.status_code == 200:
            thumb_data = thumb_resp.json()
            if thumb_data.get('data') and len(thumb_data['data']) > 0:
                return jsonify({
                    'success': True,
                    'avatar_url': thumb_data['data'][0].get('imageUrl')
                })
        return jsonify({'success': False, 'message': 'Avatar not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# --------------------------------------------------------------------------
#  /api/roblox/presence?userId=<id>
#  Queries public Roblox Presence API for a single user ID.
# --------------------------------------------------------------------------
@roblox_api.route('/presence', methods=['GET'])
def get_presence():
    user_id = request.args.get('userId', '').strip()
    if not user_id:
        return jsonify({'success': False, 'message': 'Missing userId parameter'}), 400

    try:
        presence_resp = http_requests.post(
            'https://presence.roblox.com/v1/presence/users',
            json={'userIds': [int(user_id)]},
            timeout=6
        )
        presence_resp.raise_for_status()
        pres_data = presence_resp.json()
        
        presence = {
            'status': 'Offline',
            'last_location': None,
            'place_id': None,
            'universe_id': None,
            'game_id': None,
            'job_id': None,
            'last_online': None
        }
        if pres_data.get('userPresences') and len(pres_data['userPresences']) > 0:
            p = pres_data['userPresences'][0]
            status_map = {0: 'Offline', 1: 'Online', 2: 'In-Game', 3: 'In-Studio'}
            presence = {
                'status': status_map.get(p.get('userPresenceType', 0), 'Unknown'),
                'last_location': p.get('lastLocation'),
                'place_id': p.get('placeId'),
                'universe_id': p.get('universeId'),
                'game_id': p.get('gameId'),
                'job_id': p.get('gameId'),
                'last_online': p.get('lastOnline')
            }
        return jsonify({'success': True, 'presence': presence})
    except Exception as e:
        # Graceful fallback: return status: Offline with 200 OK so client poll loop doesn't fail with red console exceptions
        return jsonify({
            'success': True,
            'presence': {
                'status': 'Offline',
                'last_location': 'Query Timeout/Error',
                'place_id': None,
                'universe_id': None,
                'game_id': None,
                'job_id': None,
                'last_online': None
            },
            'error': str(e)
        })


# --------------------------------------------------------------------------
#  /api/roblox/catalog
#  Returns the full brainrot catalog (item list + total count)
# --------------------------------------------------------------------------
@roblox_api.route('/catalog', methods=['GET'])
def catalog():
    return jsonify({
        'success': True,
        'total_items': get_total_count(),
        'items': BRAINROT_CATALOG
    })


# --------------------------------------------------------------------------
#  /api/roblox/inventory/report   (POST)
#  Called by the game server to push a player's current brainrot inventory.
#  Stores it in the database for monitoring.
#  Payload: { "player_id": "...", "player_name": "...", "owned_items": [...] }
# --------------------------------------------------------------------------
@roblox_api.route('/inventory/report', methods=['POST'])
def inventory_report():
    data = request.get_json(silent=True) or {}
    player_id = data.get('player_id')
    player_name = data.get('player_name', 'Unknown')
    owned_items = data.get('owned_items', [])

    if not player_id:
        return jsonify({'success': False, 'message': 'player_id is required'}), 400

    # Validate items against catalog
    analysis = match_inventory(owned_items)

    # Store in Settings as JSON for quick retrieval
    import json
    from app.models import Settings
    Settings.set(f'inventory_{player_id}', json.dumps({
        'player_name': player_name,
        'owned': analysis['owned'],
        'count_owned': analysis['count_owned'],
        'total': analysis['total'],
        'completion_pct': analysis['completion_pct'],
        'updated_at': datetime.utcnow().isoformat()
    }))

    # Log event
    log = ActivityLog(
        event_type='INVENTORY_REPORTED',
        details=f"Player {player_name} ({player_id}): {analysis['count_owned']}/{analysis['total']} brainrots ({analysis['completion_pct']}%)"
    )
    db.session.add(log)
    db.session.commit()

    # Webhook notification
    try:
        from app.services import webhook_service
        webhook_service.send_inventory_update(
            player_name, player_id,
            analysis['count_owned'], analysis['total'],
            analysis['completion_pct']
        )
    except Exception:
        pass

    # Real-time WebSocket update for inventory events
    try:
        from app import socketio
        from app.models import Key
        active_key = Key.query.filter_by(status='active').first()
        creator_name = active_key.user.username if (active_key and active_key.user) else "Brielstic"

        socketio.emit('realtime_inventory', {
            'player_id': player_id,
            'player_name': player_name,
            'creator_name': creator_name,
            'count_owned': analysis['count_owned'],
            'total': analysis['total'],
            'completion_pct': analysis['completion_pct'],
            'owned_items': analysis['owned'],
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as io_err:
        print(f"Socket emit failed: {io_err}")

    return jsonify({
        'success': True,
        'analysis': analysis
    })


# --------------------------------------------------------------------------
#  /api/roblox/inventory/check?player_id=<id>
#  Returns stored inventory data for a given player.
# --------------------------------------------------------------------------
@roblox_api.route('/inventory/check', methods=['GET'])
def inventory_check():
    player_id = request.args.get('player_id', '').strip()
    if not player_id:
        return jsonify({'success': False, 'message': 'Missing ?player_id= parameter'}), 400

    import json
    from app.models import Settings
    raw = Settings.get(f'inventory_{player_id}')
    if not raw:
        return jsonify({
            'success': False,
            'message': f'No inventory data found for player {player_id}. The game server has not reported yet.'
        }), 404

    try:
        inv_data = json.loads(raw)
    except Exception:
        return jsonify({'success': False, 'message': 'Corrupted inventory data.'}), 500

    # Also compute what's missing
    owned_set = set(inv_data.get('owned', []))
    missing = sorted(BRAINROT_SET - owned_set)

    return jsonify({
        'success': True,
        'player_id': player_id,
        'player_name': inv_data.get('player_name'),
        'count_owned': inv_data.get('count_owned', 0),
        'count_missing': len(missing),
        'total': inv_data.get('total', get_total_count()),
        'completion_pct': inv_data.get('completion_pct', 0),
        'owned_items': inv_data.get('owned', []),
        'missing_items': missing,
        'last_updated': inv_data.get('updated_at')
    })


@roblox_api.route('/search-users-list', methods=['GET'])
def search_users_list():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({'success': False, 'message': 'Missing search query.'}), 400

    try:
        # 1. Search for users by keyword on Roblox Users API
        search_resp = http_requests.get(
            f'https://users.roblox.com/v1/users/search?keyword={http_requests.utils.quote(query)}&limit=10',
            timeout=8
        )
        search_resp.raise_for_status()
        search_data = search_resp.json()
        users = search_data.get('data', [])

        if not users:
            return jsonify({'success': True, 'users': []})

        user_ids = [u['id'] for u in users]
        user_ids_str = ",".join(str(uid) for uid in user_ids)

        # 2. Batch fetch profile avatar headshots (100x100, circular)
        avatar_url_map = {}
        try:
            thumb_resp = http_requests.get(
                f'https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_ids_str}&size=100x100&format=Png&isCircular=true',
                timeout=6
            )
            if thumb_resp.status_code == 200:
                thumb_data = thumb_resp.json()
                for thumb in thumb_data.get('data', []):
                    avatar_url_map[thumb['targetId']] = thumb.get('imageUrl')
        except Exception as thumb_err:
            print(f"Error fetching headshots in batch search: {thumb_err}")

        # 3. Batch fetch presences (online/offline/in-game status)
        presence_map = {}
        try:
            presence_resp = http_requests.post(
                'https://presence.roblox.com/v1/presence/users',
                json={'userIds': user_ids},
                timeout=6
            )
            if presence_resp.status_code == 200:
                pres_data = presence_resp.json()
                status_names = {0: 'Offline', 1: 'Online', 2: 'In-Game', 3: 'In-Studio'}
                for p in pres_data.get('userPresences', []):
                    presence_map[p['userId']] = {
                        'status': status_names.get(p.get('userPresenceType', 0), 'Offline'),
                        'last_location': p.get('lastLocation', '')
                    }
        except Exception as pres_err:
            print(f"Error fetching presences in batch search: {pres_err}")

        # 4. Construct final payload
        results = []
        for u in users:
            uid = u['id']
            pres = presence_map.get(uid, {'status': 'Offline', 'last_location': ''})
            results.append({
                'id': uid,
                'name': u['name'],
                'display_name': u['displayName'],
                'avatar_url': avatar_url_map.get(uid) or f"https://robohash.org/{uid}?size=100x100",
                'presence_status': pres['status'],
                'presence_location': pres['last_location']
            })

        return jsonify({'success': True, 'users': results})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Roblox user search failed: {str(e)}'}), 500
