import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

/// Wraps the bits of the Supabase SDK we actually use. Keeps the rest of the
/// app from importing supabase types directly so we can swap providers later
/// without touching screens.
class AuthRepository {
  AuthRepository(this._client);

  final SupabaseClient _client;

  Session? get currentSession => _client.auth.currentSession;
  User? get currentUser => _client.auth.currentUser;

  /// Emits a new value on sign-in, sign-out, token refresh, etc.
  Stream<AuthState> authStateChanges() => _client.auth.onAuthStateChange;

  Future<AuthResponse> signIn({required String email, required String password}) {
    return _client.auth.signInWithPassword(email: email, password: password);
  }

  Future<AuthResponse> signUp({required String email, required String password}) {
    // We don't pass an emailRedirectTo here — when Supabase email confirmation
    // is enabled the user will get a verification mail and won't be signed in
    // until they click it. When confirmation is off (dev project default) the
    // call returns a usable session immediately.
    return _client.auth.signUp(email: email, password: password);
  }

  Future<void> signOut() => _client.auth.signOut();
}

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(Supabase.instance.client);
});
