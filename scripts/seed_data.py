#!/usr/bin/env python3
"""
Seed script — run INSIDE the Odoo container after module install.
Populates the database with realistic dummy data for demo/testing.

Usage (from host):
  docker exec -it odoo_server python3 /mnt/extra-addons/subscription_management/scripts/seed_data.py
"""

import xmlrpc.client
from datetime import date, timedelta
import random
import sys

# ── Connection ───────────────────────────────────────────────
URL = "http://localhost:8069"
DB = "odoo_db"
USER = "admin"
PASS = "admin"

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USER, PASS, {})
if not uid:
    print("❌ Authentication failed. Is Odoo running and the DB created?")
    sys.exit(1)

models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")


def execute(model, method, *args, **kwargs):
    return models.execute_kw(DB, uid, PASS, model, method, args, kwargs)


print("🌱 Seeding dummy data...")

# ══════════════════════════════════════════════════════════════
# 0. GRANT ADMIN THE SUBSCRIPTION MANAGER GROUP
# ══════════════════════════════════════════════════════════════
group_ids = execute("ir.model.data", "search_read",
    [("module", "=", "subscription_management"), ("name", "=", "group_subscription_manager")],
    fields=["res_id"])
if group_ids:
    manager_gid = group_ids[0]["res_id"]
    execute("res.users", "write", [uid], {"groups_id": [(4, manager_gid)]})
    print(f"  ✅ Granted Subscription Manager group to admin (gid={manager_gid})")
else:
    print("  ⚠️  Manager group not found — access errors may occur")

# ══════════════════════════════════════════════════════════════
# 1. SUBSCRIPTION PLANS
# ══════════════════════════════════════════════════════════════
plans_data = [
    {
        "name": "Starter",
        "code": "STARTER",
        "billing_cycle": "monthly",
        "price": 9.99,
        "max_domains": 1,
        "max_storage_gb": 5,
        "max_users": 1,
        "max_bandwidth_gb": 50,
        "feature_ssl": True,
        "feature_backup": False,
        "feature_support": "email",
        "sequence": 10,
    },
    {
        "name": "Professional",
        "code": "PRO",
        "billing_cycle": "quarterly",
        "price": 24.99,
        "max_domains": 5,
        "max_storage_gb": 50,
        "max_users": 10,
        "max_bandwidth_gb": 500,
        "feature_ssl": True,
        "feature_backup": True,
        "feature_support": "priority",
        "sequence": 20,
    },
    {
        "name": "Business",
        "code": "BIZ",
        "billing_cycle": "semi_annual",
        "price": 49.99,
        "max_domains": 10,
        "max_storage_gb": 100,
        "max_users": 25,
        "max_bandwidth_gb": 1000,
        "feature_ssl": True,
        "feature_backup": True,
        "feature_support": "priority",
        "sequence": 30,
    },
    {
        "name": "Enterprise",
        "code": "ENT",
        "billing_cycle": "annual",
        "price": 99.99,
        "max_domains": 50,
        "max_storage_gb": 500,
        "max_users": 100,
        "max_bandwidth_gb": 5000,
        "feature_ssl": True,
        "feature_backup": True,
        "feature_support": "dedicated",
        "sequence": 40,
    },
    {
        "name": "Ultimate",
        "code": "ULT",
        "billing_cycle": "biennial",
        "price": 179.99,
        "max_domains": 100,
        "max_storage_gb": 2000,
        "max_users": 500,
        "max_bandwidth_gb": 10000,
        "feature_ssl": True,
        "feature_backup": True,
        "feature_support": "dedicated",
        "sequence": 50,
    },
]

plan_ids = {}
for p in plans_data:
    existing = execute("subscription.plan", "search", [("code", "=", p["code"])])
    if existing:
        plan_ids[p["code"]] = existing[0]
        print(f"  ⏭  Plan '{p['name']}' already exists (id={existing[0]})")
    else:
        pid = execute("subscription.plan", "create", p)
        plan_ids[p["code"]] = pid
        print(f"  ✅ Created plan '{p['name']}' (id={pid})")

# ══════════════════════════════════════════════════════════════
# 2. TAGS
# ══════════════════════════════════════════════════════════════
tags_data = [
    {"name": "VIP", "color": 10},
    {"name": "Trial", "color": 3},
    {"name": "Reseller", "color": 4},
    {"name": "Agency", "color": 5},
    {"name": "Non-Profit", "color": 9},
    {"name": "Government", "color": 1},
    {"name": "Education", "color": 7},
    {"name": "Startup", "color": 2},
]

tag_ids = {}
for t in tags_data:
    existing = execute("subscription.tag", "search", [("name", "=", t["name"])])
    if existing:
        tag_ids[t["name"]] = existing[0]
    else:
        tid = execute("subscription.tag", "create", t)
        tag_ids[t["name"]] = tid
        print(f"  ✅ Created tag '{t['name']}' (id={tid})")

# ══════════════════════════════════════════════════════════════
# 3. CUSTOMERS (res.partner)
# ══════════════════════════════════════════════════════════════
customers_data = [
    {
        "name": "Acme Corporation",
        "email": "contact@acmecorp.com",
        "phone": "+1-555-100-2000",
        "city": "San Francisco",
        "street": "123 Market Street",
        "is_company": True,
    },
    {
        "name": "TechNova Solutions",
        "email": "info@technova.io",
        "phone": "+1-555-200-3000",
        "city": "Austin",
        "street": "456 Innovation Blvd",
        "is_company": True,
    },
    {
        "name": "GreenLeaf Organics",
        "email": "hello@greenleaf.org",
        "phone": "+44-20-7946-0958",
        "city": "London",
        "street": "78 Kensington High St",
        "is_company": True,
    },
    {
        "name": "Pinnacle Media Group",
        "email": "sales@pinnaclemedia.com",
        "phone": "+1-555-300-4000",
        "city": "New York",
        "street": "890 Broadway",
        "is_company": True,
    },
    {
        "name": "Nordic Design Studio",
        "email": "studio@nordicdesign.se",
        "phone": "+46-8-123-4567",
        "city": "Stockholm",
        "street": "12 Drottninggatan",
        "is_company": True,
    },
    {
        "name": "CloudBridge Analytics",
        "email": "support@cloudbridge.ai",
        "phone": "+1-555-400-5000",
        "city": "Seattle",
        "street": "321 Cloud Ave",
        "is_company": True,
    },
    {
        "name": "Sakura Digital",
        "email": "hello@sakuradigital.jp",
        "phone": "+81-3-1234-5678",
        "city": "Tokyo",
        "street": "5-2-1 Shibuya",
        "is_company": True,
    },
    {
        "name": "Atlas Logistics",
        "email": "ops@atlaslogistics.com",
        "phone": "+49-30-1234-5678",
        "city": "Berlin",
        "street": "45 Unter den Linden",
        "is_company": True,
    },
    {
        "name": "Bright Future Academy",
        "email": "admin@brightfuture.edu",
        "phone": "+1-555-500-6000",
        "city": "Chicago",
        "street": "200 Education Lane",
        "is_company": True,
    },
    {
        "name": "Oceanic Ventures",
        "email": "info@oceanicventures.com",
        "phone": "+61-2-9876-5432",
        "city": "Sydney",
        "street": "100 Harbour Street",
        "is_company": True,
    },
    {
        "name": "Maya Patel",
        "email": "maya.patel@gmail.com",
        "phone": "+1-555-600-7000",
        "city": "Denver",
        "is_company": False,
    },
    {
        "name": "James O'Brien",
        "email": "james.obrien@outlook.com",
        "phone": "+353-1-234-5678",
        "city": "Dublin",
        "is_company": False,
    },
    {
        "name": "Sophie Martin",
        "email": "sophie.martin@yahoo.fr",
        "phone": "+33-1-42-68-53-00",
        "city": "Paris",
        "is_company": False,
    },
    {
        "name": "Chen Wei Technologies",
        "email": "contact@chenwei.tech",
        "phone": "+86-21-1234-5678",
        "city": "Shanghai",
        "street": "888 Nanjing Road",
        "is_company": True,
    },
    {
        "name": "RedRock Mining Co",
        "email": "admin@redrockmining.com.au",
        "phone": "+61-8-9321-4567",
        "city": "Perth",
        "street": "55 St Georges Terrace",
        "is_company": True,
    },
]

partner_ids = []
for c in customers_data:
    existing = execute("res.partner", "search", [("email", "=", c["email"])])
    if existing:
        partner_ids.append(existing[0])
        print(f"  ⏭  Customer '{c['name']}' already exists (id={existing[0]})")
    else:
        pid = execute("res.partner", "create", c)
        partner_ids.append(pid)
        print(f"  ✅ Created customer '{c['name']}' (id={pid})")

# ══════════════════════════════════════════════════════════════
# 4. SUBSCRIPTIONS (25 entries across all states)
# ══════════════════════════════════════════════════════════════
today = date.today()

subscriptions_data = [
    # ── Active subscriptions ──
    {"name": "Acme Web Hosting", "partner_idx": 0, "plan": "ENT", "start_offset": -90, "state": "active", "auto_renew": True, "tags": ["VIP"]},
    {"name": "TechNova Cloud Platform", "partner_idx": 1, "plan": "PRO", "start_offset": -45, "state": "active", "auto_renew": True, "tags": ["Startup"]},
    {"name": "GreenLeaf Website", "partner_idx": 2, "plan": "STARTER", "start_offset": -20, "state": "active", "auto_renew": True, "tags": ["Non-Profit"]},
    {"name": "Pinnacle CMS Hosting", "partner_idx": 3, "plan": "BIZ", "start_offset": -120, "state": "active", "auto_renew": True, "tags": ["Agency"]},
    {"name": "Nordic Portfolio Site", "partner_idx": 4, "plan": "PRO", "start_offset": -60, "state": "active", "auto_renew": False, "tags": []},
    {"name": "CloudBridge ML Platform", "partner_idx": 5, "plan": "ULT", "start_offset": -180, "state": "active", "auto_renew": True, "tags": ["VIP"]},
    {"name": "Sakura E-Commerce", "partner_idx": 6, "plan": "ENT", "start_offset": -200, "state": "active", "auto_renew": True, "tags": []},
    {"name": "Atlas Tracking Portal", "partner_idx": 7, "plan": "BIZ", "start_offset": -30, "state": "active", "auto_renew": True, "tags": []},
    {"name": "Chen Wei SaaS Platform", "partner_idx": 13, "plan": "ULT", "start_offset": -100, "state": "active", "auto_renew": True, "tags": ["VIP", "Reseller"]},

    # ── Expiring soon (within 30 days) ──
    {"name": "Bright Future LMS", "partner_idx": 8, "plan": "PRO", "start_offset": -80, "state": "active", "auto_renew": True, "tags": ["Education"]},
    {"name": "Oceanic Dashboard", "partner_idx": 9, "plan": "BIZ", "start_offset": -170, "state": "active", "auto_renew": False, "tags": []},
    {"name": "Maya's Blog", "partner_idx": 10, "plan": "STARTER", "start_offset": -25, "state": "active", "auto_renew": True, "tags": ["Trial"]},

    # ── Expired ──
    {"name": "Acme Legacy Portal", "partner_idx": 0, "plan": "STARTER", "start_offset": -400, "state": "expired", "auto_renew": False, "tags": []},
    {"name": "James Portfolio v1", "partner_idx": 11, "plan": "STARTER", "start_offset": -60, "state": "expired", "auto_renew": False, "tags": []},
    {"name": "Sophie's Gallery", "partner_idx": 12, "plan": "PRO", "start_offset": -120, "state": "expired", "auto_renew": False, "tags": ["Trial"]},
    {"name": "RedRock Intranet", "partner_idx": 14, "plan": "ENT", "start_offset": -380, "state": "expired", "auto_renew": False, "tags": ["Government"]},

    # ── Draft ──
    {"name": "TechNova Mobile API", "partner_idx": 1, "plan": "ENT", "start_offset": 0, "state": "draft", "auto_renew": True, "tags": ["Startup"]},
    {"name": "Nordic App Backend", "partner_idx": 4, "plan": "BIZ", "start_offset": 5, "state": "draft", "auto_renew": True, "tags": []},
    {"name": "Oceanic New Project", "partner_idx": 9, "plan": "ULT", "start_offset": 10, "state": "draft", "auto_renew": True, "tags": []},

    # ── Confirmed (awaiting activation) ──
    {"name": "Pinnacle Video CDN", "partner_idx": 3, "plan": "ULT", "start_offset": 0, "state": "confirm", "auto_renew": True, "tags": ["Agency"]},
    {"name": "GreenLeaf Members Portal", "partner_idx": 2, "plan": "BIZ", "start_offset": 2, "state": "confirm", "auto_renew": True, "tags": ["Non-Profit"]},

    # ── Cancelled ──
    {"name": "Atlas Old System", "partner_idx": 7, "plan": "STARTER", "start_offset": -300, "state": "cancelled", "auto_renew": False, "tags": []},
    {"name": "CloudBridge Test Env", "partner_idx": 5, "plan": "STARTER", "start_offset": -90, "state": "cancelled", "auto_renew": False, "tags": ["Trial"]},
    {"name": "Sakura Staging", "partner_idx": 6, "plan": "PRO", "start_offset": -150, "state": "cancelled", "auto_renew": False, "tags": []},
    {"name": "Sophie's Old Blog", "partner_idx": 12, "plan": "STARTER", "start_offset": -200, "state": "cancelled", "auto_renew": False, "tags": []},
]

sub_ids = []
for s in subscriptions_data:
    start_date = (today + timedelta(days=s["start_offset"])).isoformat()
    tag_links = [(4, tag_ids[t]) for t in s.get("tags", []) if t in tag_ids]

    vals = {
        "name": s["name"],
        "partner_id": partner_ids[s["partner_idx"]],
        "plan_id": plan_ids[s["plan"]],
        "date_start": start_date,
        "is_auto_renew": s["auto_renew"],
    }
    if tag_links:
        vals["tag_ids"] = tag_links

    existing = execute("subscription.subscription", "search", [("name", "=", s["name"])])
    if existing:
        sub_ids.append(existing[0])
        print(f"  ⏭  Subscription '{s['name']}' exists (id={existing[0]})")
        continue

    sid = execute("subscription.subscription", "create", vals)
    sub_ids.append(sid)

    # Transition through states via direct write (XML-RPC can't marshal None returns from button methods)
    target = s["state"]
    if target in ("confirm", "active", "expiring_soon", "expired", "cancelled"):
        execute("subscription.subscription", "write", [sid], {"state": "confirm"})
    if target in ("active", "expiring_soon", "expired", "cancelled"):
        execute("subscription.subscription", "write", [sid], {"state": "active"})
    if target == "expired":
        execute("subscription.subscription", "write", [sid], {"state": "expired"})
    if target == "cancelled":
        execute("subscription.subscription", "write", [sid], {"state": "cancelled"})

    label = s["state"].upper()
    print(f"  ✅ Created subscription '{s['name']}' → {label} (id={sid})")

# ══════════════════════════════════════════════════════════════
# 5. DOMAINS (linked to subscriptions)
# ══════════════════════════════════════════════════════════════
domains_data = [
    # Acme Web Hosting (Enterprise — up to 50 domains)
    {"sub_name": "Acme Web Hosting", "name": "acmecorp.com", "is_primary": True, "state": "active", "ssl": True, "dns": "Cloudflare", "ip": "104.21.45.12", "registrar": "GoDaddy"},
    {"sub_name": "Acme Web Hosting", "name": "shop.acmecorp.com", "is_primary": False, "state": "active", "ssl": True, "dns": "Cloudflare", "ip": "104.21.45.13", "registrar": "GoDaddy"},
    {"sub_name": "Acme Web Hosting", "name": "api.acmecorp.com", "is_primary": False, "state": "active", "ssl": True, "dns": "Cloudflare", "ip": "104.21.45.14", "registrar": "GoDaddy"},

    # TechNova Cloud Platform (Pro — up to 5)
    {"sub_name": "TechNova Cloud Platform", "name": "technova.io", "is_primary": True, "state": "active", "ssl": True, "dns": "AWS Route53", "ip": "52.14.123.45", "registrar": "Namecheap"},
    {"sub_name": "TechNova Cloud Platform", "name": "app.technova.io", "is_primary": False, "state": "active", "ssl": True, "dns": "AWS Route53", "ip": "52.14.123.46", "registrar": "Namecheap"},

    # GreenLeaf Website (Starter — 1 domain)
    {"sub_name": "GreenLeaf Website", "name": "greenleaf.org", "is_primary": True, "state": "active", "ssl": True, "dns": "Google DNS", "ip": "216.58.214.206", "registrar": "Google Domains"},

    # Pinnacle CMS (Business — up to 10)
    {"sub_name": "Pinnacle CMS Hosting", "name": "pinnaclemedia.com", "is_primary": True, "state": "active", "ssl": True, "dns": "Cloudflare", "ip": "172.67.182.31", "registrar": "Namecheap"},
    {"sub_name": "Pinnacle CMS Hosting", "name": "news.pinnaclemedia.com", "is_primary": False, "state": "active", "ssl": True, "dns": "Cloudflare", "ip": "172.67.182.32", "registrar": "Namecheap"},
    {"sub_name": "Pinnacle CMS Hosting", "name": "blog.pinnaclemedia.com", "is_primary": False, "state": "propagating", "ssl": False, "dns": "Cloudflare", "ip": "172.67.182.33", "registrar": "Namecheap"},

    # Nordic Portfolio
    {"sub_name": "Nordic Portfolio Site", "name": "nordicdesign.se", "is_primary": True, "state": "active", "ssl": True, "dns": "Loopia", "ip": "94.236.35.100", "registrar": "Loopia"},

    # CloudBridge ML (Ultimate)
    {"sub_name": "CloudBridge ML Platform", "name": "cloudbridge.ai", "is_primary": True, "state": "active", "ssl": True, "dns": "AWS Route53", "ip": "54.200.12.34", "registrar": "AWS"},
    {"sub_name": "CloudBridge ML Platform", "name": "dashboard.cloudbridge.ai", "is_primary": False, "state": "active", "ssl": True, "dns": "AWS Route53", "ip": "54.200.12.35", "registrar": "AWS"},
    {"sub_name": "CloudBridge ML Platform", "name": "api.cloudbridge.ai", "is_primary": False, "state": "active", "ssl": True, "dns": "AWS Route53", "ip": "54.200.12.36", "registrar": "AWS"},

    # Sakura E-Commerce
    {"sub_name": "Sakura E-Commerce", "name": "sakuradigital.jp", "is_primary": True, "state": "active", "ssl": True, "dns": "Onamae", "ip": "210.140.92.183", "registrar": "Onamae"},
    {"sub_name": "Sakura E-Commerce", "name": "store.sakuradigital.jp", "is_primary": False, "state": "active", "ssl": True, "dns": "Onamae", "ip": "210.140.92.184", "registrar": "Onamae"},

    # Atlas Tracking
    {"sub_name": "Atlas Tracking Portal", "name": "atlaslogistics.com", "is_primary": True, "state": "active", "ssl": True, "dns": "Hetzner", "ip": "138.201.45.67", "registrar": "DENIC"},

    # Bright Future LMS (expiring soon)
    {"sub_name": "Bright Future LMS", "name": "brightfuture.edu", "is_primary": True, "state": "active", "ssl": True, "dns": "Cloudflare", "ip": "104.21.90.50", "registrar": "GoDaddy"},

    # Maya's Blog
    {"sub_name": "Maya's Blog", "name": "mayawrites.com", "is_primary": True, "state": "active", "ssl": True, "dns": "Cloudflare", "ip": "104.21.90.60", "registrar": "Namecheap"},

    # Chen Wei SaaS
    {"sub_name": "Chen Wei SaaS Platform", "name": "chenwei.tech", "is_primary": True, "state": "active", "ssl": True, "dns": "Alibaba DNS", "ip": "47.74.12.34", "registrar": "Alibaba Cloud"},
    {"sub_name": "Chen Wei SaaS Platform", "name": "app.chenwei.tech", "is_primary": False, "state": "active", "ssl": True, "dns": "Alibaba DNS", "ip": "47.74.12.35", "registrar": "Alibaba Cloud"},
    {"sub_name": "Chen Wei SaaS Platform", "name": "api.chenwei.tech", "is_primary": False, "state": "active", "ssl": True, "dns": "Alibaba DNS", "ip": "47.74.12.36", "registrar": "Alibaba Cloud"},
    {"sub_name": "Chen Wei SaaS Platform", "name": "docs.chenwei.tech", "is_primary": False, "state": "propagating", "ssl": False, "dns": "Alibaba DNS", "ip": "", "registrar": "Alibaba Cloud"},

    # Expired — James Portfolio
    {"sub_name": "James Portfolio v1", "name": "jamesobrien.ie", "is_primary": True, "state": "inactive", "ssl": False, "dns": "Blacknight", "ip": "", "registrar": "Blacknight"},

    # Expired — Sophie's Gallery
    {"sub_name": "Sophie's Gallery", "name": "sophiemartin.fr", "is_primary": True, "state": "inactive", "ssl": False, "dns": "OVH", "ip": "", "registrar": "OVH"},

    # Expired — RedRock
    {"sub_name": "RedRock Intranet", "name": "redrockmining.com.au", "is_primary": True, "state": "inactive", "ssl": False, "dns": "VentraIP", "ip": "", "registrar": "VentraIP"},

    # Cancelled — pending domains
    {"sub_name": "Atlas Old System", "name": "atlas-old.de", "is_primary": True, "state": "inactive", "ssl": False, "dns": "Hetzner", "ip": "", "registrar": "DENIC"},
    {"sub_name": "Sakura Staging", "name": "staging.sakuradigital.jp", "is_primary": True, "state": "inactive", "ssl": False, "dns": "Onamae", "ip": "", "registrar": "Onamae"},
]

# Build sub name → id map
sub_name_map = {}
for i, s in enumerate(subscriptions_data):
    sub_name_map[s["name"]] = sub_ids[i]

domain_count = 0
for d in domains_data:
    sub_id = sub_name_map.get(d["sub_name"])
    if not sub_id:
        print(f"  ⚠️  Subscription '{d['sub_name']}' not found, skipping domain '{d['name']}'")
        continue

    existing = execute("subscription.domain", "search", [("name", "=", d["name"])])
    if existing:
        print(f"  ⏭  Domain '{d['name']}' already exists")
        continue

    ssl_expiry = (today + timedelta(days=random.randint(60, 365))).isoformat() if d["ssl"] else False
    reg_date = (today - timedelta(days=random.randint(180, 1000))).isoformat()

    vals = {
        "name": d["name"],
        "subscription_id": sub_id,
        "is_primary": d["is_primary"],
        "state": d["state"],
        "ssl_enabled": d["ssl"],
        "ssl_expiry_date": ssl_expiry,
        "ssl_issuer": "Let's Encrypt" if d["ssl"] else False,
        "dns_provider": d["dns"],
        "ip_address": d["ip"] or False,
        "registrar": d["registrar"],
        "registration_date": reg_date,
        "nameserver_1": f"ns1.{d['dns'].lower().replace(' ', '')}.com",
        "nameserver_2": f"ns2.{d['dns'].lower().replace(' ', '')}.com",
    }
    execute("subscription.domain", "create", vals)
    domain_count += 1

print(f"  ✅ Created {domain_count} domains")

# ══════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════
total_plans = len(execute("subscription.plan", "search", []))
total_subs = len(execute("subscription.subscription", "search", []))
total_domains = len(execute("subscription.domain", "search", []))
total_partners = len(partner_ids)
total_tags = len(execute("subscription.tag", "search", []))

print(f"""
{'='*55}
🎉  SEED DATA COMPLETE
{'='*55}
  📋 Plans:          {total_plans}
  🏷️  Tags:           {total_tags}
  👥 Customers:      {total_partners}
  📦 Subscriptions:  {total_subs}
  🌐 Domains:        {total_domains}

  States breakdown:
    Draft:          {len(execute("subscription.subscription", "search", [("state", "=", "draft")]))}
    Confirmed:      {len(execute("subscription.subscription", "search", [("state", "=", "confirm")]))}
    Active:         {len(execute("subscription.subscription", "search", [("state", "=", "active")]))}
    Expiring Soon:  {len(execute("subscription.subscription", "search", [("state", "=", "expiring_soon")]))}
    Expired:        {len(execute("subscription.subscription", "search", [("state", "=", "expired")]))}
    Cancelled:      {len(execute("subscription.subscription", "search", [("state", "=", "cancelled")]))}
{'='*55}
""")
