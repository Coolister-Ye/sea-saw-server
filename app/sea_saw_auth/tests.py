from django.test import TestCase

from .models import Role, User


class RoleModelTests(TestCase):

    def setUp(self):
        # Create roles
        self.parent_role = Role.objects.create(role_name="Parent Role")
        self.child_role1 = Role.objects.create(
            role_name="Child Role 1", parent=self.parent_role
        )
        self.child_role2 = Role.objects.create(
            role_name="Child Role 2", parent=self.parent_role
        )
        self.grandchild_role = Role.objects.create(
            role_name="Grandchild Role", parent=self.child_role1
        )

        # Create some users
        self.user1 = User.objects.create_user(username="user1", role=self.parent_role)
        self.user2 = User.objects.create_user(username="user2", role=self.child_role1)
        self.user3 = User.objects.create_user(username="user3", role=self.child_role2)
        self.user4 = User.objects.create_user(
            username="user4", role=self.grandchild_role
        )

    def test_get_all_descendants(self):
        """Test the get_all_descendants method."""
        descendants = self.parent_role.get_all_descendants()
        self.assertEqual(
            set(descendants), {self.child_role1, self.child_role2, self.grandchild_role}
        )

    def test_get_all_visible_users_with_peer_visibility(self):
        """Test the get_all_visible_users method with peer visibility."""
        # Set child_role1's is_peer_visible to True
        self.child_role1.is_peer_visible = True
        self.child_role1.save()

        # Call from user2 (who has child_role1)
        visible_users = self.user2.get_all_visible_users()
        # Should see: self (user2), peers in same role, and descendants (user4)
        self.assertEqual(
            set(visible_users), {self.user2, self.user4}
        )

    def test_get_all_visible_users_no_peers(self):
        """Test the get_all_visible_users method without peer visibility."""
        # is_peer_visible is False by default
        visible_users = self.user2.get_all_visible_users()
        # Should see: self (user2) and descendants (user4)
        self.assertEqual(
            set(visible_users), {self.user2, self.user4}
        )

    def test_get_all_visible_users_no_descendants(self):
        """Test the get_all_visible_users when the role has no descendants."""
        visible_users = self.user4.get_all_visible_users()
        # Should only see self
        self.assertEqual(
            set(visible_users), {self.user4}
        )

    def test_get_all_visible_users_from_user(self):
        """Test the get_all_visible_users from a user"""
        visible_users = self.user1.get_all_visible_users()
        self.assertEqual(
            set(visible_users), {self.user1, self.user2, self.user3, self.user4}
        )
