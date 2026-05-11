import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../data/auth_repository.dart';

/// Streams the current Supabase auth state. `data.session` is `null` when the
/// user is signed out and a `Session` (with access token + claims) when signed
/// in. UI and the Dio interceptor watch this.
final authStateStreamProvider = StreamProvider<AuthState>((ref) {
  final repo = ref.watch(authRepositoryProvider);
  return repo.authStateChanges();
});

/// Synchronous accessor for the current session. Reads from the Supabase
/// client (which keeps a cached copy on disk) so it works on cold start before
/// the auth stream has emitted.
final currentSessionProvider = Provider<Session?>((ref) {
  // Re-evaluate whenever the auth stream ticks so widgets watching this
  // rebuild on sign-in / sign-out.
  ref.watch(authStateStreamProvider);
  return ref.watch(authRepositoryProvider).currentSession;
});

final currentUserProvider = Provider<User?>((ref) {
  ref.watch(authStateStreamProvider);
  return ref.watch(authRepositoryProvider).currentUser;
});

final isSignedInProvider = Provider<bool>((ref) {
  return ref.watch(currentSessionProvider) != null;
});
