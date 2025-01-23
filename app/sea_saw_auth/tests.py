from django.test import TestCase
from .models import Role, User


class RoleModelTests(TestCase):

    def setUp(self):
        # Create roles
        self.parent_role = Role.objects.create(name='Parent Role')
        self.child_role1 = Role.objects.create(name='Child Role 1', parent=self.parent_role)
        self.child_role2 = Role.objects.create(name='Child Role 2', parent=self.parent_role)
        self.grandchild_role = Role.objects.create(name='Grandchild Role', parent=self.child_role1)

        # Create some users
        self.user1 = User.objects.create_user(username='user1', role=self.parent_role)
        self.user2 = User.objects.create_user(username='user2', role=self.child_role1)
        self.user3 = User.objects.create_user(username='user3', role=self.child_role2)
        self.user4 = User.objects.create_user(username='user4', role=self.grandchild_role)

    def test_get_descendant_ids(self):
        """Test the get_descendant_ids method."""
        descendant_ids = self.parent_role.get_descendant_ids()
        self.assertEqual(set(descendant_ids), {self.child_role1.id, self.child_role2.id, self.grandchild_role.id})

    def test_get_all_descendants(self):
        """Test the get_all_descendants method."""
        descendants = self.parent_role.get_all_descendants()
        self.assertEqual(set(descendants), {self.child_role1, self.child_role2, self.grandchild_role})

    def test_get_peers(self):
        """Test the get_peers method."""
        peers = self.child_role1.get_peers()
        self.assertEqual(list(peers), [self.child_role2])  # child_role1's peer is child_role2

    def test_get_all_visible_users(self):
        """Test the get_all_visible_users method."""
        # Set child_role1's is_peer_visible to True
        self.child_role1.is_peer_visible = True
        self.child_role1.save()

        visible_users = self.child_role1.get_all_visible_users()
        self.assertEqual(set(visible_users), {self.user2, self.user3, self.user4})  # child_role1, child_role2 and grandchild_role users are visible

    def test_get_all_visible_users_no_peers(self):
        """Test the get_all_visible_users method without peers visible."""
        visible_users = self.child_role1.get_all_visible_users()
        self.assertEqual(set(visible_users), {self.user2, self.user4})  # child_role1, grandchild_role's user is visible

    def test_get_all_visible_users_no_descendants(self):
        """Test the get_all_visible_users when the role has no descendants."""
        visible_users = self.grandchild_role.get_all_visible_users()
        self.assertEqual(visible_users, [self.user4])  # Only grandchild_role's user is visible

    def test_get_all_visible_users_from_user(self):
        """Test the get_all_visible_users from a user"""
        visible_users = self.user1.get_all_visible_users()
        self.assertEqual(set(visible_users), {self.user1, self.user2, self.user3, self.user4})