#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  Subscription Management — Docker Quick Start
# ═══════════════════════════════════════════════════════════════
#
#  Starts Odoo 17 + PostgreSQL 16, installs the module,
#  creates a database, and seeds it with 25 subscriptions,
#  15 customers, 27 domains, 5 plans, and 8 tags.
#
#  Usage:   chmod +x start.sh && ./start.sh
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

COMPOSE_FILE="docker-compose.yml"
DB_NAME="odoo_db"
ADMIN_PASS="admin"
ODOO_URL="http://localhost:8069"

echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  🚀 Subscription Management — Docker Quick Start ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"

# ── Step 1: Start containers ─────────────────────────────────
echo -e "\n${YELLOW}[1/5] Starting Docker containers...${NC}"
docker compose -f "$COMPOSE_FILE" up -d --build

# ── Step 2: Wait for Odoo to be ready ────────────────────────
echo -e "${YELLOW}[2/5] Waiting for Odoo to start (this may take 30-60s on first run)...${NC}"
MAX_WAIT=120
ELAPSED=0
until curl -s -o /dev/null -w "%{http_code}" "$ODOO_URL/web/login" | grep -q "200"; do
    sleep 3
    ELAPSED=$((ELAPSED + 3))
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo -e "${RED}❌ Odoo failed to start within ${MAX_WAIT}s. Check logs:${NC}"
        echo "   docker compose logs odoo"
        exit 1
    fi
    printf "   Waiting... (%ds)\r" $ELAPSED
done
echo -e "   ${GREEN}✅ Odoo is running!${NC}"

# ── Step 3: Create database ──────────────────────────────────
echo -e "${YELLOW}[3/5] Creating database '${DB_NAME}'...${NC}"
DB_EXISTS=$(docker exec odoo_server python3 -c "
import xmlrpc.client
dbs = xmlrpc.client.ServerProxy('$ODOO_URL/xmlrpc/2/db').list()
print('yes' if '$DB_NAME' in dbs else 'no')
" 2>/dev/null || echo "no")

if [ "$DB_EXISTS" = "yes" ]; then
    echo -e "   ${GREEN}⏭  Database '${DB_NAME}' already exists${NC}"
else
    docker exec odoo_server python3 -c "
import xmlrpc.client
db = xmlrpc.client.ServerProxy('$ODOO_URL/xmlrpc/2/db')
db.create_database('admin_master_pwd', '$DB_NAME', True, 'en_US', '$ADMIN_PASS', 'admin')
print('Database created')
"
    echo -e "   ${GREEN}✅ Database '${DB_NAME}' created${NC}"
    echo -e "   Waiting for database initialization..."
    sleep 10
fi

# ── Step 4: Install the module ────────────────────────────────
echo -e "${YELLOW}[4/5] Installing subscription_management module...${NC}"
docker exec odoo_server python3 -c "
import xmlrpc.client

url = '$ODOO_URL'
db = '$DB_NAME'
uid = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common').authenticate(db, 'admin', '$ADMIN_PASS', {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Update module list
models.execute_kw(db, uid, '$ADMIN_PASS', 'ir.module.module', 'update_list', [])

# Find and install
mod_ids = models.execute_kw(db, uid, '$ADMIN_PASS', 'ir.module.module', 'search',
    [[('name', '=', 'subscription_management')]])

if not mod_ids:
    print('ERROR: Module not found. Check addons path.')
    exit(1)

state = models.execute_kw(db, uid, '$ADMIN_PASS', 'ir.module.module', 'read',
    [mod_ids], {'fields': ['state']})[0]['state']

if state == 'installed':
    print('Module already installed — upgrading...')
    models.execute_kw(db, uid, '$ADMIN_PASS', 'ir.module.module', 'button_immediate_upgrade', [mod_ids])
else:
    print(f'Module state: {state} — installing...')
    models.execute_kw(db, uid, '$ADMIN_PASS', 'ir.module.module', 'button_immediate_install', [mod_ids])

print('Module ready!')
"
echo -e "   ${GREEN}✅ Module installed${NC}"

# Wait for Odoo to stabilize after install
sleep 5

# ── Step 5: Seed dummy data ──────────────────────────────────
echo -e "${YELLOW}[5/5] Seeding dummy data...${NC}"
docker exec odoo_server python3 /mnt/extra-addons/subscription_management/scripts/seed_data.py

echo -e "\n${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ ALL DONE! Your subscription app is ready.     ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  🌐 URL:       ${CYAN}${ODOO_URL}${NC}"
echo -e "  📁 Database:  ${CYAN}${DB_NAME}${NC}"
echo -e "  👤 Login:     ${CYAN}admin${NC}"
echo -e "  🔑 Password:  ${CYAN}admin${NC}"
echo ""
echo -e "  ${YELLOW}Open ${ODOO_URL} in your browser and log in!${NC}"
echo ""
