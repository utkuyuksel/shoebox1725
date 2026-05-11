import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../../app/theme.dart';
import '../data/auth_repository.dart';

enum _Mode { signIn, signUp }

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();

  _Mode _mode = _Mode.signIn;
  bool _busy = false;
  String? _error;
  String? _info;
  bool _obscure = true;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    HapticFeedback.selectionClick();
    setState(() {
      _busy = true;
      _error = null;
      _info = null;
    });
    try {
      final repo = ref.read(authRepositoryProvider);
      final email = _emailCtrl.text.trim();
      final password = _passwordCtrl.text;
      if (_mode == _Mode.signIn) {
        await repo.signIn(email: email, password: password);
      } else {
        final res = await repo.signUp(email: email, password: password);
        if (!mounted) return;
        if (res.session == null) {
          // Email confirmation required → show info, don't navigate.
          setState(() {
            _info = 'Check your inbox to confirm your email, then sign in.';
            _mode = _Mode.signIn;
          });
          return;
        }
      }
      if (!mounted) return;
      // Auth stream will redrive AuthGate; pop back to whatever pushed us.
      if (context.canPop()) {
        context.pop();
      } else {
        context.go('/');
      }
    } on AuthException catch (e) {
      setState(() => _error = e.message);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isSignUp = _mode == _Mode.signUp;
    return Scaffold(
      appBar: AppBar(
        leading: context.canPop()
            ? IconButton(
                icon: const Icon(Icons.close_rounded),
                onPressed: () => context.pop(),
              )
            : null,
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 8, 24, 32),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Icon(Icons.bolt_rounded,
                        size: 48, color: ShoeboxColors.accent),
                    const SizedBox(height: 12),
                    Text(
                      isSignUp ? 'Create your account' : 'Welcome back',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.w800,
                          ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      isSignUp
                          ? 'Sign up to save watchlists and unlock premium picks.'
                          : 'Sign in to continue your research.',
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: ShoeboxColors.textMid),
                    ),
                    const SizedBox(height: 28),
                    TextFormField(
                      controller: _emailCtrl,
                      keyboardType: TextInputType.emailAddress,
                      autocorrect: false,
                      enableSuggestions: false,
                      textInputAction: TextInputAction.next,
                      decoration: _decoration('Email', Icons.alternate_email),
                      validator: (v) {
                        final s = v?.trim() ?? '';
                        if (s.isEmpty) return 'Required';
                        if (!s.contains('@') || !s.contains('.')) {
                          return 'Enter a valid email';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _passwordCtrl,
                      obscureText: _obscure,
                      autocorrect: false,
                      enableSuggestions: false,
                      textInputAction: TextInputAction.done,
                      onFieldSubmitted: (_) => _submit(),
                      decoration: _decoration('Password', Icons.lock_outline).copyWith(
                        suffixIcon: IconButton(
                          icon: Icon(_obscure
                              ? Icons.visibility_outlined
                              : Icons.visibility_off_outlined),
                          color: ShoeboxColors.textMid,
                          onPressed: () => setState(() => _obscure = !_obscure),
                        ),
                      ),
                      validator: (v) {
                        if (v == null || v.isEmpty) return 'Required';
                        if (isSignUp && v.length < 6) {
                          return 'At least 6 characters';
                        }
                        return null;
                      },
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: 12),
                      _Banner(text: _error!, danger: true),
                    ],
                    if (_info != null) ...[
                      const SizedBox(height: 12),
                      _Banner(text: _info!, danger: false),
                    ],
                    const SizedBox(height: 20),
                    FilledButton(
                      onPressed: _busy ? null : _submit,
                      style: FilledButton.styleFrom(
                        backgroundColor: ShoeboxColors.accent,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12)),
                      ),
                      child: _busy
                          ? const SizedBox(
                              height: 18,
                              width: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor:
                                    AlwaysStoppedAnimation<Color>(Colors.white),
                              ),
                            )
                          : Text(isSignUp ? 'Sign up' : 'Sign in',
                              style: const TextStyle(
                                  fontWeight: FontWeight.w700, fontSize: 15)),
                    ),
                    const SizedBox(height: 16),
                    TextButton(
                      onPressed: _busy
                          ? null
                          : () => setState(() {
                                _mode = isSignUp ? _Mode.signIn : _Mode.signUp;
                                _error = null;
                                _info = null;
                              }),
                      child: Text.rich(
                        TextSpan(children: [
                          TextSpan(
                              text: isSignUp
                                  ? 'Already have an account? '
                                  : "Don't have an account? ",
                              style: const TextStyle(color: ShoeboxColors.textMid)),
                          TextSpan(
                              text: isSignUp ? 'Sign in' : 'Sign up',
                              style: const TextStyle(
                                  color: ShoeboxColors.accent,
                                  fontWeight: FontWeight.w700)),
                        ]),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  InputDecoration _decoration(String label, IconData icon) {
    return InputDecoration(
      labelText: label,
      prefixIcon: Icon(icon, color: ShoeboxColors.textMid),
      filled: true,
      fillColor: ShoeboxColors.surface,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide.none,
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: ShoeboxColors.accent, width: 1.4),
      ),
    );
  }
}

class _Banner extends StatelessWidget {
  final String text;
  final bool danger;
  const _Banner({required this.text, required this.danger});

  @override
  Widget build(BuildContext context) {
    final bg = danger
        ? ShoeboxColors.danger.withValues(alpha: 0.12)
        : ShoeboxColors.accentSoft;
    final fg = danger ? ShoeboxColors.danger : ShoeboxColors.accent;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Icon(danger ? Icons.error_outline : Icons.info_outline,
              size: 18, color: fg),
          const SizedBox(width: 8),
          Expanded(
            child: Text(text, style: TextStyle(color: fg, fontSize: 13)),
          ),
        ],
      ),
    );
  }
}
