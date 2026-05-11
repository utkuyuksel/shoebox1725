// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Portuguese (`pt`).
class AppLocalizationsPt extends AppLocalizations {
  AppLocalizationsPt([String locale = 'pt']) : super(locale);

  @override
  String get appTitle => 'Shoebox';

  @override
  String get navLeagues => 'Ligas';

  @override
  String get navWatchlist => 'Lista';

  @override
  String get navAccount => 'Conta';

  @override
  String get sportFootball => 'Futebol';

  @override
  String get sportBasketball => 'Basquete';

  @override
  String get homePopular => 'Populares';

  @override
  String get homeAllCompetitions => 'Todas as competições';

  @override
  String get homeRefereesTooltip => 'Árbitros';

  @override
  String get homeEmpty => 'Ainda não há ligas disponíveis para este esporte.';

  @override
  String get homeOneCompetition => '1 competição';

  @override
  String homeCompetitionsCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count competições',
      one: '1 competição',
      zero: 'Sem competições',
    );
    return '$_temp0';
  }

  @override
  String get watchlistTitle => 'Lista';

  @override
  String get watchlistSignedOutTitle => 'Entre para usar sua lista';

  @override
  String get watchlistSignedOutBody =>
      'Salve partidas e mantenha-as sincronizadas entre dispositivos.';

  @override
  String get watchlistEmpty =>
      'Toque no marcador em qualquer partida para adicioná-la aqui.';

  @override
  String get watchlistSheetTitle => 'Entre para salvar partidas';

  @override
  String get watchlistSheetBody =>
      'Sua lista sincroniza entre dispositivos após entrar.';

  @override
  String watchlistFailed(String detail) {
    return 'Falha: $detail';
  }

  @override
  String get loginWelcomeBack => 'Bem-vindo de volta';

  @override
  String get loginCreateAccount => 'Crie sua conta';

  @override
  String get loginSubtitleSignUp =>
      'Cadastre-se para salvar sua lista e liberar picks premium.';

  @override
  String get loginSubtitleSignIn => 'Entre para continuar sua análise.';

  @override
  String get loginEmail => 'Email';

  @override
  String get loginPassword => 'Senha';

  @override
  String get loginErrorRequired => 'Obrigatório';

  @override
  String get loginErrorEmail => 'Insira um email válido';

  @override
  String get loginErrorPasswordShort => 'Pelo menos 6 caracteres';

  @override
  String get loginConfirmInbox =>
      'Confira sua caixa para confirmar seu email e depois entre.';

  @override
  String get loginSignIn => 'Entrar';

  @override
  String get loginSignUp => 'Cadastrar';

  @override
  String get loginPromptToSignUp => 'Não tem uma conta? ';

  @override
  String get loginPromptToSignIn => 'Já tem uma conta? ';

  @override
  String get settingsTitle => 'Ajustes';

  @override
  String get settingsSectionAccount => 'Conta';

  @override
  String get settingsSectionSubscription => 'Assinatura';

  @override
  String get settingsSectionAbout => 'Sobre';

  @override
  String get settingsSectionLanguage => 'Idioma';

  @override
  String get settingsSignInCta => 'Entre ou cadastre-se';

  @override
  String get settingsSignInSubtitle => 'Salve sua lista e libere premium';

  @override
  String settingsSignedInSubtitle(String idShort) {
    return 'ID do usuário: $idShort…';
  }

  @override
  String get settingsSignOut => 'Sair';

  @override
  String get settingsPremiumActive => 'Premium ativo';

  @override
  String get settingsPremiumActiveSubtitle =>
      'Você tem acesso a todos os recursos';

  @override
  String get settingsPremiumUpgrade => 'Atualize para Premium';

  @override
  String get settingsPremiumUpgradeSubtitle =>
      'Hit rates, splits, médias completas';

  @override
  String settingsAboutVersion(String version) {
    return 'Versão $version';
  }

  @override
  String get settingsSignOutDialogTitle => 'Sair?';

  @override
  String get settingsSignOutDialogBody =>
      'Você precisará entrar novamente para acessar o premium.';

  @override
  String get settingsLanguageSystem => 'Padrão do sistema';

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
  String get paywallHeroTitle => 'Desbloqueie toda a vantagem';

  @override
  String get paywallHeroSubtitle =>
      'Hit rates, splits e médias completas da temporada.';

  @override
  String get paywallBenefitHitRatesTitle => 'Desdobramento de hit rates';

  @override
  String get paywallBenefitHitRatesBody =>
      'Mais/menos 2.5, ambos marcam, linhas AH — por time e por liga.';

  @override
  String get paywallBenefitSplitsTitle => 'Casa / fora';

  @override
  String get paywallBenefitSplitsBody =>
      'Veja onde os times rendem acima ou abaixo do mercado.';

  @override
  String get paywallBenefitRefereeTitle => 'Análise de árbitro';

  @override
  String get paywallBenefitRefereeBody =>
      'Cartões, pênaltis e padrões históricos por arbitragem.';

  @override
  String get paywallNoPlans =>
      'Ainda não há planos de assinatura configurados. Adicione uma oferta no painel do RevenueCat para habilitar as compras.';

  @override
  String get paywallContinue => 'Continuar';

  @override
  String get paywallRestore => 'Restaurar compras';

  @override
  String get paywallUnlocked => 'Premium desbloqueado.';

  @override
  String get paywallRestored => 'Compras restauradas.';

  @override
  String get paywallNothingToRestore => 'Nada a restaurar.';

  @override
  String get paywallLegal =>
      'As assinaturas renovam automaticamente até serem canceladas. Gerencie na App Store ou Play Store.';

  @override
  String paywallGateLabel(String tier) {
    return 'Desbloquear com $tier';
  }

  @override
  String get paywallSheetTitle => 'Desbloqueie esta seção';

  @override
  String get paywallSheetBody =>
      'Assista a um anúncio curto para abri-la neste jogo, ou atualize para acesso ilimitado.';

  @override
  String get paywallWatchAdTitle => 'Assistir anúncio de 30s';

  @override
  String get paywallWatchAdSubtitle => 'Desbloqueia esta seção neste jogo';

  @override
  String get paywallUpgradeTitle => 'Atualize para Premium';

  @override
  String get paywallUpgradeSubtitle => 'Acesso ilimitado, sem anúncios';

  @override
  String get commonCancel => 'Cancelar';

  @override
  String get commonClose => 'Fechar';

  @override
  String get commonTryAgain => 'Tentar novamente';

  @override
  String get commonRetry => 'Tentar novamente';

  @override
  String get commonGenericError => 'Não foi possível carregar';

  @override
  String get commonNothingHere => 'Ainda não há nada para mostrar.';

  @override
  String get commonLive => 'AO VIVO';

  @override
  String get commonFinalShort => 'FT';

  @override
  String get onboarding1Title => 'Pesquisa pré-jogo, simplificada';

  @override
  String get onboarding1Body =>
      'Hit rates, splits, padrões do árbitro — os dados que o apostador sharp consulta antes de cada jogo, em uma tela.';

  @override
  String get onboarding2Title => 'Grátis + premium, de forma justa';

  @override
  String get onboarding2Body =>
      'Assista a um anúncio curto para desbloquear uma seção premium em um jogo, ou atualize para acesso ilimitado.';

  @override
  String get onboarding3Title => 'Sua lista, seus alertas';

  @override
  String get onboarding3Body =>
      'Salve partidas e avisaremos uma hora antes do início. Sincroniza entre dispositivos quando você entrar.';

  @override
  String get onboardingNext => 'Próximo';

  @override
  String get onboardingDone => 'Começar';

  @override
  String get onboardingSkip => 'Pular';

  @override
  String get matchSectionSeasonAverages => 'Médias da temporada';

  @override
  String get matchSectionHitRate => 'Hit rate · temporada';

  @override
  String get matchSectionRadar => 'Perfil de forma';

  @override
  String get matchSectionReferee => 'Árbitro · histórico';

  @override
  String get matchRefereeNoHistory => 'Sem histórico';

  @override
  String matchTrendCardTitle(String teamLabel, int n) {
    return '$teamLabel · últimos $n jogos';
  }

  @override
  String matchTrendSeasonAvg(String avg) {
    return 'Média temporada: $avg por jogo';
  }

  @override
  String get matchTrendNoData => 'Sem dados para esta métrica.';

  @override
  String get metricGoalsFor => 'Gols a favor';

  @override
  String get metricGoalsAgainst => 'Gols sofridos';

  @override
  String get metricCorners => 'Escanteios';

  @override
  String get metricYellowCards => 'Cartões amarelos';

  @override
  String get metricShots => 'Chutes';

  @override
  String get metricPoints => 'Pontos';

  @override
  String get metricPointsAllowed => 'Pontos sofridos';

  @override
  String get metricRebounds => 'Rebotes';

  @override
  String get metricAssists => 'Assistências';

  @override
  String get metricThreesMade => 'Cestas de 3';

  @override
  String get settingsNotificationsToggle => 'Abrir ajustes de notificações';

  @override
  String get settingsNotificationsSubtitle => 'Gerencie os lembretes';

  @override
  String get settingsShowOnboarding => 'Ver tour de boas-vindas';

  @override
  String get settingsShowOnboardingSubtitle => 'Reveja a intro de 3 telas';
}
