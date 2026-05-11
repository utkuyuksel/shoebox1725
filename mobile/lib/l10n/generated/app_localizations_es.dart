// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Spanish Castilian (`es`).
class AppLocalizationsEs extends AppLocalizations {
  AppLocalizationsEs([String locale = 'es']) : super(locale);

  @override
  String get appTitle => 'Shoebox';

  @override
  String get navLeagues => 'Ligas';

  @override
  String get navWatchlist => 'Mi lista';

  @override
  String get navAccount => 'Cuenta';

  @override
  String get sportFootball => 'Fútbol';

  @override
  String get sportBasketball => 'Baloncesto';

  @override
  String get homePopular => 'Populares';

  @override
  String get homeAllCompetitions => 'Todas las competiciones';

  @override
  String get homeRefereesTooltip => 'Árbitros';

  @override
  String get homeEmpty => 'Aún no hay ligas disponibles para este deporte.';

  @override
  String get homeOneCompetition => '1 competición';

  @override
  String homeCompetitionsCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count competiciones',
      one: '1 competición',
      zero: 'Sin competiciones',
    );
    return '$_temp0';
  }

  @override
  String get watchlistTitle => 'Mi lista';

  @override
  String get watchlistSignedOutTitle => 'Inicia sesión para usar tu lista';

  @override
  String get watchlistSignedOutBody =>
      'Guarda partidos y sincronízalos entre dispositivos.';

  @override
  String get watchlistEmpty =>
      'Toca el marcador en cualquier partido para añadirlo aquí.';

  @override
  String get watchlistSheetTitle => 'Inicia sesión para guardar partidos';

  @override
  String get watchlistSheetBody =>
      'Tu lista se sincroniza entre dispositivos al iniciar sesión.';

  @override
  String watchlistFailed(String detail) {
    return 'Error: $detail';
  }

  @override
  String get loginWelcomeBack => 'Bienvenido de nuevo';

  @override
  String get loginCreateAccount => 'Crea tu cuenta';

  @override
  String get loginSubtitleSignUp =>
      'Regístrate para guardar tu lista y desbloquear las picks premium.';

  @override
  String get loginSubtitleSignIn =>
      'Inicia sesión para seguir con tu análisis.';

  @override
  String get loginEmail => 'Email';

  @override
  String get loginPassword => 'Contraseña';

  @override
  String get loginErrorRequired => 'Obligatorio';

  @override
  String get loginErrorEmail => 'Introduce un email válido';

  @override
  String get loginErrorPasswordShort => 'Mínimo 6 caracteres';

  @override
  String get loginConfirmInbox =>
      'Revisa tu bandeja para confirmar tu email y luego inicia sesión.';

  @override
  String get loginSignIn => 'Iniciar sesión';

  @override
  String get loginSignUp => 'Registrarse';

  @override
  String get loginPromptToSignUp => '¿No tienes cuenta? ';

  @override
  String get loginPromptToSignIn => '¿Ya tienes cuenta? ';

  @override
  String get settingsTitle => 'Ajustes';

  @override
  String get settingsSectionAccount => 'Cuenta';

  @override
  String get settingsSectionSubscription => 'Suscripción';

  @override
  String get settingsSectionAbout => 'Acerca de';

  @override
  String get settingsSectionLanguage => 'Idioma';

  @override
  String get settingsSignInCta => 'Inicia sesión o regístrate';

  @override
  String get settingsSignInSubtitle => 'Guarda tu lista y desbloquea premium';

  @override
  String settingsSignedInSubtitle(String idShort) {
    return 'ID de usuario: $idShort…';
  }

  @override
  String get settingsSignOut => 'Cerrar sesión';

  @override
  String get settingsPremiumActive => 'Premium activo';

  @override
  String get settingsPremiumActiveSubtitle =>
      'Tienes acceso a todas las funciones';

  @override
  String get settingsPremiumUpgrade => 'Mejora a Premium';

  @override
  String get settingsPremiumUpgradeSubtitle =>
      'Hit rates, splits, promedios completos';

  @override
  String settingsAboutVersion(String version) {
    return 'Versión $version';
  }

  @override
  String get settingsSignOutDialogTitle => '¿Cerrar sesión?';

  @override
  String get settingsSignOutDialogBody =>
      'Tendrás que iniciar sesión otra vez para acceder a premium.';

  @override
  String get settingsLanguageSystem => 'Predeterminado del sistema';

  @override
  String get settingsLanguageEnglish => 'English';

  @override
  String get settingsLanguageTurkish => 'Türkçe';

  @override
  String get settingsLanguageSpanish => 'Español';

  @override
  String get settingsLanguagePortuguese => 'Português';

  @override
  String get paywallTitle => 'Premium';

  @override
  String get paywallHeroTitle => 'Desbloquea toda la ventaja';

  @override
  String get paywallHeroSubtitle =>
      'Hit rates, splits y promedios de temporada completos.';

  @override
  String get paywallBenefitHitRatesTitle => 'Desglose de hit rates';

  @override
  String get paywallBenefitHitRatesBody =>
      'Más/menos 2.5, ambos marcan, líneas AH — por equipo y por liga.';

  @override
  String get paywallBenefitSplitsTitle => 'Casa / visitante';

  @override
  String get paywallBenefitSplitsBody =>
      'Ve dónde los equipos rinden por encima o por debajo del mercado.';

  @override
  String get paywallBenefitRefereeTitle => 'Análisis de árbitro';

  @override
  String get paywallBenefitRefereeBody =>
      'Tarjetas, penaltis y patrones históricos por colegiado.';

  @override
  String get paywallNoPlans =>
      'Todavía no hay planes de suscripción configurados. Añade una oferta en el panel de RevenueCat para activar las compras.';

  @override
  String get paywallContinue => 'Continuar';

  @override
  String get paywallRestore => 'Restaurar compras';

  @override
  String get paywallUnlocked => 'Premium desbloqueado.';

  @override
  String get paywallRestored => 'Compras restauradas.';

  @override
  String get paywallNothingToRestore => 'Nada que restaurar.';

  @override
  String get paywallLegal =>
      'Las suscripciones se renuevan automáticamente hasta su cancelación. Gestiona desde App Store o Play Store.';

  @override
  String paywallGateLabel(String tier) {
    return 'Desbloquear con $tier';
  }

  @override
  String get paywallSheetTitle => 'Desbloquea esta sección';

  @override
  String get paywallSheetBody =>
      'Mira un anuncio corto para abrirla en este partido, o mejora para acceso ilimitado.';

  @override
  String get paywallWatchAdTitle => 'Ver un anuncio de 30 segundos';

  @override
  String get paywallWatchAdSubtitle =>
      'Desbloquea esta sección en este partido';

  @override
  String get paywallUpgradeTitle => 'Mejora a Premium';

  @override
  String get paywallUpgradeSubtitle => 'Acceso ilimitado, sin anuncios';

  @override
  String get commonCancel => 'Cancelar';

  @override
  String get commonClose => 'Cerrar';

  @override
  String get commonTryAgain => 'Reintentar';

  @override
  String get commonRetry => 'Reintentar';

  @override
  String get commonGenericError => 'No se ha podido cargar';

  @override
  String get commonNothingHere => 'Aún no hay nada que mostrar.';

  @override
  String get commonLive => 'EN VIVO';

  @override
  String get commonFinalShort => 'FT';

  @override
  String get onboarding1Title => 'Análisis pre-partido, simplificado';

  @override
  String get onboarding1Body =>
      'Hit rates, splits, patrones del árbitro — los datos que el apostador sharp consulta antes de cada partido, en una pantalla.';

  @override
  String get onboarding2Title => 'Gratis + premium, de forma justa';

  @override
  String get onboarding2Body =>
      'Mira un anuncio corto para desbloquear una sección premium en un partido, o mejora para acceso ilimitado.';

  @override
  String get onboarding3Title => 'Tu lista, tus alertas';

  @override
  String get onboarding3Body =>
      'Guarda partidos y te avisaremos una hora antes del pitido inicial. Sincroniza entre dispositivos al iniciar sesión.';

  @override
  String get onboardingNext => 'Siguiente';

  @override
  String get onboardingDone => 'Empezar';

  @override
  String get onboardingSkip => 'Saltar';

  @override
  String get matchSectionSeasonAverages => 'Promedios de temporada';

  @override
  String get matchSectionHitRate => 'Hit rate · temporada';

  @override
  String get matchSectionRadar => 'Perfil de forma';

  @override
  String get matchSectionReferee => 'Árbitro · historial';

  @override
  String get matchRefereeNoHistory => 'Sin historial';

  @override
  String matchTrendCardTitle(String teamLabel, int n) {
    return '$teamLabel · últimos $n partidos';
  }

  @override
  String matchTrendSeasonAvg(String avg) {
    return 'Promedio temporada: $avg por partido';
  }

  @override
  String get matchTrendNoData => 'Sin datos para esta métrica.';

  @override
  String get metricGoalsFor => 'Goles a favor';

  @override
  String get metricGoalsAgainst => 'Goles en contra';

  @override
  String get metricCorners => 'Córners';

  @override
  String get metricYellowCards => 'Tarjetas amarillas';

  @override
  String get metricShots => 'Disparos';

  @override
  String get metricPoints => 'Puntos';

  @override
  String get metricPointsAllowed => 'Puntos recibidos';

  @override
  String get metricRebounds => 'Rebotes';

  @override
  String get metricAssists => 'Asistencias';

  @override
  String get metricThreesMade => 'Triples';

  @override
  String get settingsNotificationsToggle => 'Abrir ajustes de notificaciones';

  @override
  String get settingsNotificationsSubtitle => 'Gestiona los recordatorios';

  @override
  String get settingsShowOnboarding => 'Ver tutorial de nuevo';

  @override
  String get settingsShowOnboardingSubtitle => 'Repite la intro de 3 pantallas';
}
