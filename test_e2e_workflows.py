import unittest
from app import app
from app.firebase_db import rooms_col, bookings_col, restaurant_tables_col


class TestEndToEndWorkflows(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def set_session(self, email="test.staff@nur-e-haya.com", role="admin"):
        with self.client.session_transaction() as sess:
            sess['user_id'] = f"uid_{email}"
            sess['user_email'] = email
            sess['user_role'] = role
            sess['property_id'] = 'prop_1'

    def test_workflow_staff_invitation_accept(self):
        """Test token-gated staff registration flow with password policy."""
        # 1. Admin sends invitation
        self.set_session(email="admin@nur-e-haya.com", role="admin")
        invite_res = self.client.post('/api/admin/staff/invite',
            json={"email": "chef_new@nur-e-haya.com", "role": "kitchen", "department": "Kitchen & Dining"})
        self.assertEqual(invite_res.status_code, 200)
        invite_data = invite_res.get_json()
        self.assertTrue(invite_data.get('ok'))
        token = invite_data['data']['invite_token']

        # Clear session
        with self.client.session_transaction() as sess:
            sess.clear()

        # 2. View invite page
        view_res = self.client.get(f'/invite/{token}')
        self.assertEqual(view_res.status_code, 200)
        self.assertIn(b'Staff Invite Acceptance', view_res.data)

        # 3. Fail on weak password
        weak_res = self.client.post('/api/auth/invite/accept',
            json={"token": token, "password": "weak"})
        self.assertEqual(weak_res.status_code, 400)

        # 4. Succeed with strong password
        strong_res = self.client.post('/api/auth/invite/accept',
            json={"token": token, "password": "RoyalSecret@2026", "name": "Head Chef Kabir"})
        self.assertEqual(strong_res.status_code, 200)
        strong_data = strong_res.get_json()
        self.assertTrue(strong_data.get('ok'))
        self.assertEqual(strong_data['data']['role'], 'kitchen')
        self.assertEqual(strong_data['data']['redirect_url'], '/staff/kitchen')

        # 5. Token cannot be reused
        reuse_res = self.client.post('/api/auth/invite/accept',
            json={"token": token, "password": "RoyalSecret@2026"})
        self.assertEqual(reuse_res.status_code, 400)

    def test_workflow_checkout_housekeeping_turnover(self):
        """Test checkout auto-generating housekeeping turnover task, and cleaning setting room available."""
        self.set_session(email="frontdesk@nur-e-haya.com", role="front_desk")

        # 1. Setup room and booking
        room_ref = rooms_col().document('rm_test_turnover')
        room_ref.set({
            "number": "505",
            "type": "Suite",
            "status": "occupied",
            "price_per_night": 6500,
            "is_active": True
        })

        b_ref = bookings_col().document('bk_test_turnover')
        b_ref.set({
            "room_id": "rm_test_turnover",
            "room_number": "505",
            "status": "checked_in",
            "guest_name": "Lord Sterling",
            "total_price": 13000
        })

        # 2. Front desk check out
        co_res = self.client.post('/api/front-desk/checkout',
            json={"booking_id": "bk_test_turnover"})
        self.assertEqual(co_res.status_code, 200)
        co_data = co_res.get_json()
        self.assertTrue(co_data.get('ok'))
        self.assertEqual(co_data['data']['status'], 'checked_out')
        hk_task_id = co_data['data']['housekeeping_task_id']
        self.assertTrue(hk_task_id)

        # Check room status is now dirty / cleaning
        rm_after_co = room_ref.get().to_dict()
        self.assertIn(rm_after_co['status'], ['dirty', 'cleaning'])

        # 3. Housekeeper completes turnover cleaning
        self.set_session(email="cleaner@nur-e-haya.com", role="housekeeping")
        task_update_res = self.client.patch(f'/api/housekeeping/tasks/{hk_task_id}',
            json={"status": "done"})
        self.assertEqual(task_update_res.status_code, 200)
        self.assertTrue(task_update_res.get_json().get('ok'))

        # Check room status is auto-promoted to available
        rm_after_clean = room_ref.get().to_dict()
        self.assertEqual(rm_after_clean['status'], 'available')

    def test_workflow_housekeeping_issue_and_maintenance_unblock(self):
        """Test reporting housekeeping issue blocks room to maintenance, and ticket resolve unblocks it."""
        self.set_session(email="housekeeper@nur-e-haya.com", role="housekeeping")

        room_ref = rooms_col().document('rm_test_maint')
        room_ref.set({
            "number": "602",
            "type": "Deluxe",
            "status": "available",
            "price_per_night": 4500,
            "is_active": True
        })

        # 1. Report issue from housekeeping
        issue_res = self.client.post('/api/housekeeping/tasks/tsk_turnover_602/report-issue',
            json={
                "room_id": "rm_test_maint",
                "room_number": "602",
                "issue_type": "plumbing",
                "severity": "urgent",
                "description": "Bathroom pipe leakage detected"
            })
        self.assertEqual(issue_res.status_code, 200)
        issue_data = issue_res.get_json()
        self.assertTrue(issue_data.get('ok'))
        ticket_id = issue_data['data']['maintenance_ticket_id']

        # Verify room is blocked to maintenance
        rm_maint = room_ref.get().to_dict()
        self.assertEqual(rm_maint['status'], 'maintenance')

        # 2. Maintenance engineer resolves ticket
        self.set_session(email="engineer@nur-e-haya.com", role="maintenance")

        # Must require resolution_note
        no_note_res = self.client.patch(f'/api/maintenance/tickets/{ticket_id}',
            json={"status": "resolved"})
        self.assertEqual(no_note_res.status_code, 400)

        # Supply resolution note and resolve
        resolve_res = self.client.patch(f'/api/maintenance/tickets/{ticket_id}',
            json={"status": "resolved", "resolution_note": "Replaced copper connector and leak test passed"})
        self.assertEqual(resolve_res.status_code, 200)
        resolve_data = resolve_res.get_json()
        self.assertTrue(resolve_data.get('ok'))
        self.assertTrue(resolve_data['data'].get('room_unblocked'))

        # Verify room is unblocked back to available
        rm_resolved = room_ref.get().to_dict()
        self.assertEqual(rm_resolved['status'], 'available')

    def test_tape_chart_and_drawer_api(self):
        """Test tape chart matrix API and slide-over room drawer API."""
        self.set_session(email="frontdesk@nur-e-haya.com", role="front_desk")

        # 1. Tape chart matrix
        tc_res = self.client.get('/api/front-desk/tape-chart')
        self.assertEqual(tc_res.status_code, 200)
        tc_data = tc_res.get_json()
        self.assertTrue(tc_data.get('ok'))
        self.assertIn('dates', tc_data['data'])
        self.assertIn('rooms', tc_data['data'])
        self.assertEqual(len(tc_data['data']['dates']), 14)

        # 2. Room drawer API
        rooms_col().document('rm_drawer_test').set({
            "number": "701",
            "type": "Presidential Penthouse",
            "status": "available",
            "price_per_night": 12000,
            "floor": 7
        })

        drawer_res = self.client.get('/api/front-desk/rooms/rm_drawer_test/drawer')
        self.assertEqual(drawer_res.status_code, 200)
        drawer_data = drawer_res.get_json()
        self.assertTrue(drawer_data.get('ok'))
        self.assertEqual(drawer_data['data']['room']['number'], '701')

    def test_admin_crud_and_shift_punch(self):
        """Test full REST CRUD on Rooms, Facilities, Menu and Shift Punching."""
        self.set_session(email="admin@nur-e-haya.com", role="admin")

        # 1. Facility CRUD
        create_fac = self.client.post('/api/admin/facilities',
            json={
                "name": "Skyline Infinity Pool",
                "category": "wellness",
                "price_per_hour": 1500,
                "capacity": 20
            })
        self.assertEqual(create_fac.status_code, 200)
        fac_id = create_fac.get_json()['data']['id']

        patch_fac = self.client.patch(f'/api/admin/facilities/{fac_id}',
            json={"price_per_hour": 1800})
        self.assertEqual(patch_fac.status_code, 200)

        del_fac = self.client.delete(f'/api/admin/facilities/{fac_id}')
        self.assertEqual(del_fac.status_code, 200)

        # 2. Menu Item CRUD
        create_menu = self.client.post('/api/admin/menu',
            json={
                "name": "Truffle Infused Risotto",
                "category": "Main Course",
                "price": 850,
                "is_veg": True
            })
        self.assertEqual(create_menu.status_code, 200)
        menu_id = create_menu.get_json()['data']['id']

        patch_menu = self.client.patch(f'/api/admin/menu/{menu_id}',
            json={"price": 950})
        self.assertEqual(patch_menu.status_code, 200)

        del_menu = self.client.delete(f'/api/admin/menu/{menu_id}')
        self.assertEqual(del_menu.status_code, 200)

        # 3. Shift Clock In / Clock Out
        self.set_session(email="clerk@nur-e-haya.com", role="front_desk")
        clock_in = self.client.post('/api/staff/shift/clock',
            json={"action": "clock_in"})
        self.assertEqual(clock_in.status_code, 200)
        self.assertEqual(clock_in.get_json()['data']['action'], 'clock_in')

        clock_out = self.client.post('/api/staff/shift/clock',
            json={"action": "clock_out"})
        self.assertEqual(clock_out.status_code, 200)
        self.assertEqual(clock_out.get_json()['data']['action'], 'clock_out')

    def test_food_menu_and_live_kitchen_waiter_order_flow(self):
        """Test 150+ menu items, kitchen KDS cook advance, waiter pickup, and table turnover lifecycle."""
        # 1. Menu API checks
        menu_res = self.client.get('/api/menu-items')
        self.assertEqual(menu_res.status_code, 200)
        items = menu_res.get_json()['data']
        self.assertGreaterEqual(len(items), 150, "Should have 150+ real seeded menu items")

        # Verify category coverage
        categories = {i.get('category', '').lower() for i in items}
        self.assertTrue({'starters', 'mains', 'desserts', 'beverages', 'snacks'}.issubset(categories))

        # Check sample item properties
        sample = items[0]
        self.assertTrue(sample.get('name'))
        self.assertGreater(sample.get('price', 0), 0)
        self.assertTrue(sample.get('image_url') or sample.get('img'))
        self.assertIn(sample.get('diet'), ['veg', 'non-veg'])

        # 2. Guest places food order for Restaurant Table T-04
        self.set_session(email="guest.diner@example.com", role="guest")
        order_payload = {
            "table_number": "T-04",
            "payment_method": "upi",
            "items": [
                {"item_id": sample['id'], "name": sample['name'], "price": sample['price'], "qty": 2}
            ]
        }
        order_res = self.client.post('/api/orders', json=order_payload)
        self.assertEqual(order_res.status_code, 200)
        order_data = order_res.get_json()['data']
        order_id = order_data['order_id']
        self.assertEqual(order_data['status'], 'received')

        # Verify Table T-04 is automatically occupied
        tbl_doc = restaurant_tables_col().document('tbl_T-04').get()
        self.assertTrue(tbl_doc.exists)
        self.assertEqual(tbl_doc.to_dict()['status'], 'occupied')

        # 3. Cook views KDS and advances order: received -> preparing -> ready
        self.set_session(email="chef@nur-e-haya.com", role="chef")
        kds_res = self.client.get('/api/kitchen/orders')
        self.assertEqual(kds_res.status_code, 200)

        # Start cooking
        prep_res = self.client.patch(f'/api/orders/{order_id}/status', json={"status": "preparing"})
        self.assertEqual(prep_res.status_code, 200)

        # Mark plated & ready for waiter pass
        ready_res = self.client.patch(f'/api/orders/{order_id}/status', json={"status": "ready"})
        self.assertEqual(ready_res.status_code, 200)

        # 4. Waiter receives alert, picks up and delivers to Table T-04
        self.set_session(email="waiter@nur-e-haya.com", role="waiter")
        pickup_res = self.client.patch(f'/api/orders/{order_id}/status', json={"status": "delivering"})
        self.assertEqual(pickup_res.status_code, 200)

        deliver_res = self.client.patch(f'/api/orders/{order_id}/status', json={"status": "delivered"})
        self.assertEqual(deliver_res.status_code, 200)

        # Delivery transitions table to bill_pending
        tbl_after_delivery = restaurant_tables_col().document('tbl_T-04').get().to_dict()
        self.assertEqual(tbl_after_delivery['status'], 'bill_pending')

        # 5. Bill is settled -> Table transitions to busing (needs clearing/cleaning)
        bill_res = self.client.patch(f'/api/orders/{order_id}/status', json={"status": "paid"})
        self.assertEqual(bill_res.status_code, 200)
        tbl_after_paid = restaurant_tables_col().document('tbl_T-04').get().to_dict()
        self.assertEqual(tbl_after_paid['status'], 'busing')

        # 6. Steward cleans and resets table -> Table transitions to available
        clean_res = self.client.patch('/api/dining/tables/tbl_T-04/status', json={"status": "available"})
        self.assertEqual(clean_res.status_code, 200)
        tbl_final = restaurant_tables_col().document('tbl_T-04').get().to_dict()
        self.assertEqual(tbl_final['status'], 'available')

    def test_guest_room_needs_and_departure_turnover_flow(self):
        """Test guest in-room requests (cleaning, dnd) and departure triggering turnover cleaning."""
        self.set_session(email="guest.resident@example.com", role="guest")

        # 1. Guest requests "Make Up Room" (Cleaning)
        req_res = self.client.post('/api/guest/room-service/request', json={
            "service_type": "cleaning",
            "room_number": "RW-301",
            "notes": "Please refresh fresh towels and mineral water"
        })
        self.assertEqual(req_res.status_code, 200)
        req_data = req_res.get_json()['data']
        self.assertEqual(req_data['status'], 'cleaning_dispatched')
        self.assertTrue(req_data['task_id'])

        # 2. Guest toggles DND
        dnd_res = self.client.post('/api/guest/room-service/request', json={
            "service_type": "dnd",
            "room_number": "RW-301",
            "dnd": True
        })
        self.assertEqual(dnd_res.status_code, 200)
        self.assertTrue(dnd_res.get_json()['data']['dnd'])

        # 3. Guest signals departure / Express Checkout ("I'm Leaving Now")
        leave_res = self.client.post('/api/guest/room-service/request', json={
            "service_type": "checkout_leaving",
            "room_number": "RW-301",
            "notes": "Keys left on bedside console"
        })
        self.assertEqual(leave_res.status_code, 200)
        leave_data = leave_res.get_json()['data']
        self.assertEqual(leave_data['status'], 'checkout_processed')
        turnover_task_id = leave_data['task_id']
        self.assertTrue(turnover_task_id)

        # Verify Room RW-301 status is updated to cleaning
        rm_doc = rooms_col().document('rm_RW-301').get()
        self.assertEqual(rm_doc.to_dict()['status'], 'cleaning')

        # 4. Housekeeper sees urgent turnover cleaning task and completes it
        self.set_session(email="housekeeper@nur-e-haya.com", role="housekeeping")
        done_res = self.client.patch(f'/api/housekeeping/tasks/{turnover_task_id}', json={"status": "done"})
        self.assertEqual(done_res.status_code, 200)

        # Verify Room RW-301 automatically returns to available
        rm_cleaned = rooms_col().document('rm_RW-301').get().to_dict()
        self.assertEqual(rm_cleaned['status'], 'available')

    def test_frontdesk_mark_clean_endpoint(self):
        """Test front desk mark-clean endpoint resolving by flat code or number."""
        self.set_session(email="frontdesk@nur-e-haya.com", role="front_desk")
        rooms_col().document('rm_HW-101').update({"status": "dirty"})

        res = self.client.post('/api/front-desk/mark-clean', json={"room_id": "HW-101"})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()['ok'])
        self.assertEqual(rooms_col().document('rm_HW-101').get().to_dict()['status'], 'available')


if __name__ == '__main__':
    unittest.main()


