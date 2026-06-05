// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Shoebox';

  @override
  String get navLeagues => 'Leagues';

  @override
  String get navWatchlist => 'Watchlist';

  @override
  String get navAccount => 'Account';

  @override
  String get sportFootball => 'Football';

  @override
  String get sportBasketball => 'Basketball';

  @override
  String get homePopular => 'Popular';

  @override
  String get homeAllCompetitions => 'All competitions';

  @override
  String get homeRefereesTooltip => 'Referees';

  @override
  String get homeEmpty => 'No leagues available for this sport yet.';

  @override
  String get homeOneCompetition => '1 competition';

  @override
  String homeCompetitionsCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count competitions',
      one: '1 competition',
      zero: 'No competitions',
    );
    return '$_temp0';
  }

  @override
  String get watchlistTitle => 'Watchlist';

  @override
  String get watchlistSignedOutTitle => 'Sign in to use the watchlist';

  @override
  String get watchlistSignedOutBody =>
      'Bookmark fixtures and keep them synced across devices.';

  @override
  String get watchlistEmpty =>
      'Tap the bookmark on any fixture to add it here.';

  @override
  String get watchlistSheetTitle => 'Sign in to save fixtures';

  @override
  String get watchlistSheetBody =>
      'Your watchlist syncs across devices once you sign in.';

  @override
  String watchlistFailed(String detail) {
    return 'Failed: $detail';
  }

  @override
  String get loginWelcomeBack => 'Welcome back';

  @override
  String get loginCreateAccount => 'Create your account';

  @override
  String get loginSubtitleSignUp =>
      'Sign up to save watchlists and unlock premium picks.';

  @override
  String get loginSubtitleSignIn => 'Sign in to continue your research.';

  @override
  String get loginEmail => 'Email';

  @override
  String get loginPassword => 'Password';

  @override
  String get loginErrorRequired => 'Required';

  @override
  String get loginErrorEmail => 'Enter a valid email';

  @override
  String get loginErrorPasswordShort => 'At least 6 characters';

  @override
  String get loginConfirmInbox =>
      'Check your inbox to confirm your email, then sign in.';

  @override
  String get loginSignIn => 'Sign in';

  @override
  String get loginSignUp => 'Sign up';

  @override
  String get loginPromptToSignUp => 'Don\'t have an account? ';

  @override
  String get loginPromptToSignIn => 'Already have an account? ';

  @override
  String get settingsTitle => 'Settings';

  @override
  String get settingsSectionAccount => 'Account';

  @override
  String get settingsSectionSubscription => 'Subscription';

  @override
  String get settingsSectionAbout => 'About';

  @override
  String get settingsSectionLanguage => 'Language';

  @override
  String get settingsSignInCta => 'Sign in or sign up';

  @override
  String get settingsSignInSubtitle => 'Save your watchlist and unlock premium';

  @override
  String settingsSignedInSubtitle(String idShort) {
    return 'User ID: $idShort…';
  }

  @override
  String get settingsSignOut => 'Sign out';

  @override
  String get settingsPremiumActive => 'Premium active';

  @override
  String get settingsPremiumActiveSubtitle => 'You have access to all features';

  @override
  String get settingsPremiumUpgrade => 'Upgrade to Premium';

  @override
  String get settingsPremiumUpgradeSubtitle =>
      'Hit rates, splits, full averages';

  @override
  String settingsAboutVersion(String version) {
    return 'Version $version';
  }

  @override
  String get settingsSignOutDialogTitle => 'Sign out?';

  @override
  String get settingsSignOutDialogBody =>
      'You\'ll need to sign in again to access premium.';

  @override
  String get settingsLanguageSystem => 'System default';

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
  String get paywallHeroTitle => 'Unlock the full edge';

  @override
  String get paywallHeroSubtitle =>
      'Hit rates, splits, and full season averages.';

  @override
  String get paywallBenefitHitRatesTitle => 'Hit-rate breakdowns';

  @override
  String get paywallBenefitHitRatesBody =>
      'Over/under 2.5, BTTS, AH lines — per team and per league.';

  @override
  String get paywallBenefitSplitsTitle => 'Home / away splits';

  @override
  String get paywallBenefitSplitsBody =>
      'See where teams over- and under-perform vs the market.';

  @override
  String get paywallBenefitRefereeTitle => 'Referee deep-dive';

  @override
  String get paywallBenefitRefereeBody =>
      'Cards, penalties, and historical patterns by official.';

  @override
  String get paywallNoPlans =>
      'No subscription plans are configured yet. Add an offering in the RevenueCat dashboard to enable purchases.';

  @override
  String get paywallContinue => 'Continue';

  @override
  String get paywallRestore => 'Restore purchases';

  @override
  String get paywallUnlocked => 'Premium unlocked.';

  @override
  String get paywallRestored => 'Purchases restored.';

  @override
  String get paywallNothingToRestore => 'Nothing to restore.';

  @override
  String get paywallLegal =>
      'Subscriptions renew automatically until cancelled. Manage in the App Store or Play Store.';

  @override
  String paywallGateLabel(String tier) {
    return 'Unlock with $tier';
  }

  @override
  String get paywallSheetTitle => 'Unlock this section';

  @override
  String get paywallSheetBody =>
      'Watch a short ad to open it for this match, or upgrade for unlimited access.';

  @override
  String get paywallWatchAdTitle => 'Watch a 30-second ad';

  @override
  String get paywallWatchAdSubtitle => 'Unlocks this section for this match';

  @override
  String get paywallUpgradeTitle => 'Upgrade to Premium';

  @override
  String get paywallUpgradeSubtitle => 'Unlimited access, no ads';

  @override
  String get commonCancel => 'Cancel';

  @override
  String get commonClose => 'Close';

  @override
  String get commonTryAgain => 'Try again';

  @override
  String get commonRetry => 'Try again';

  @override
  String get commonGenericError => 'Couldn\'t load this';

  @override
  String get commonNothingHere => 'Nothing to show yet.';

  @override
  String get commonLive => 'LIVE';

  @override
  String get commonFinalShort => 'FT';

  @override
  String get onboarding1Title => 'Pre-match research, simplified';

  @override
  String get onboarding1Body =>
      'Hit rates, splits, referee patterns — the data sharp bettors look up before every match, on one screen.';

  @override
  String get onboarding2Title => 'Free + premium, fairly';

  @override
  String get onboarding2Body =>
      'Watch a short ad to unlock any premium section for a match, or upgrade for unlimited access.';

  @override
  String get onboarding3Title => 'Your watchlist, your alerts';

  @override
  String get onboarding3Body =>
      'Bookmark fixtures and we\'ll remind you an hour before kickoff. Syncs across devices once you sign in.';

  @override
  String get onboardingNext => 'Next';

  @override
  String get onboardingDone => 'Get started';

  @override
  String get onboardingSkip => 'Skip';

  @override
  String get matchSectionSeasonAverages => 'Season averages';

  @override
  String get matchSectionHitRate => 'Hit rate · season';

  @override
  String get matchSectionRadar => 'Form fingerprint';

  @override
  String get matchSectionReferee => 'Referee · history';

  @override
  String get matchRefereeNoHistory => 'No history';

  @override
  String get matchSectionH2H => 'Head to head';

  @override
  String get matchH2HEmpty => 'No previous meetings';

  @override
  String get matchH2HAvgTotal => 'Avg total';

  @override
  String get standingsTitle => 'Standings';

  @override
  String get standingsEmpty => 'No standings available yet.';

  @override
  String get standingsTeam => 'Team';

  @override
  String get standingsPlayedShort => 'P';

  @override
  String get standingsGoalDiffShort => 'GD';

  @override
  String get standingsPointsShort => 'Pts';

  @override
  String get standingsWinPctShort => 'Win%';

  @override
  String get standingsWinLossShort => 'W-L';

  @override
  String get standingsForm => 'Form';

  @override
  String matchTrendCardTitle(String teamLabel, int n) {
    return '$teamLabel · last $n matches';
  }

  @override
  String matchTrendSeasonAvg(String avg) {
    return 'Season avg: $avg per game';
  }

  @override
  String get matchTrendNoData => 'No data for this metric.';

  @override
  String get metricGoalsFor => 'Goals for';

  @override
  String get metricGoalsAgainst => 'Goals against';

  @override
  String get metricCorners => 'Corners';

  @override
  String get metricYellowCards => 'Yellow cards';

  @override
  String get metricShots => 'Shots';

  @override
  String get metricPoints => 'Points';

  @override
  String get metricPointsAllowed => 'Points allowed';

  @override
  String get metricRebounds => 'Rebounds';

  @override
  String get metricAssists => 'Assists';

  @override
  String get metricThreesMade => '3-pointers made';

  @override
  String get settingsNotificationsToggle => 'Open system Notification settings';

  @override
  String get settingsNotificationsSubtitle => 'Manage kickoff reminders';

  @override
  String get settingsShowOnboarding => 'Replay the welcome tour';

  @override
  String get settingsShowOnboardingSubtitle => 'See the 3-screen intro again';
}
