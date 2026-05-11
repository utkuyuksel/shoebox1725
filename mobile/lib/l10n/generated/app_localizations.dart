import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_es.dart';
import 'app_localizations_pt.dart';
import 'app_localizations_tr.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'generated/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('es'),
    Locale('pt'),
    Locale('tr'),
  ];

  /// No description provided for @appTitle.
  ///
  /// In en, this message translates to:
  /// **'Shoebox'**
  String get appTitle;

  /// No description provided for @navLeagues.
  ///
  /// In en, this message translates to:
  /// **'Leagues'**
  String get navLeagues;

  /// No description provided for @navWatchlist.
  ///
  /// In en, this message translates to:
  /// **'Watchlist'**
  String get navWatchlist;

  /// No description provided for @navAccount.
  ///
  /// In en, this message translates to:
  /// **'Account'**
  String get navAccount;

  /// No description provided for @sportFootball.
  ///
  /// In en, this message translates to:
  /// **'Football'**
  String get sportFootball;

  /// No description provided for @sportBasketball.
  ///
  /// In en, this message translates to:
  /// **'Basketball'**
  String get sportBasketball;

  /// No description provided for @homePopular.
  ///
  /// In en, this message translates to:
  /// **'Popular'**
  String get homePopular;

  /// No description provided for @homeAllCompetitions.
  ///
  /// In en, this message translates to:
  /// **'All competitions'**
  String get homeAllCompetitions;

  /// No description provided for @homeRefereesTooltip.
  ///
  /// In en, this message translates to:
  /// **'Referees'**
  String get homeRefereesTooltip;

  /// No description provided for @homeEmpty.
  ///
  /// In en, this message translates to:
  /// **'No leagues available for this sport yet.'**
  String get homeEmpty;

  /// No description provided for @homeOneCompetition.
  ///
  /// In en, this message translates to:
  /// **'1 competition'**
  String get homeOneCompetition;

  /// No description provided for @homeCompetitionsCount.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =0{No competitions} =1{1 competition} other{{count} competitions}}'**
  String homeCompetitionsCount(int count);

  /// No description provided for @watchlistTitle.
  ///
  /// In en, this message translates to:
  /// **'Watchlist'**
  String get watchlistTitle;

  /// No description provided for @watchlistSignedOutTitle.
  ///
  /// In en, this message translates to:
  /// **'Sign in to use the watchlist'**
  String get watchlistSignedOutTitle;

  /// No description provided for @watchlistSignedOutBody.
  ///
  /// In en, this message translates to:
  /// **'Bookmark fixtures and keep them synced across devices.'**
  String get watchlistSignedOutBody;

  /// No description provided for @watchlistEmpty.
  ///
  /// In en, this message translates to:
  /// **'Tap the bookmark on any fixture to add it here.'**
  String get watchlistEmpty;

  /// No description provided for @watchlistSheetTitle.
  ///
  /// In en, this message translates to:
  /// **'Sign in to save fixtures'**
  String get watchlistSheetTitle;

  /// No description provided for @watchlistSheetBody.
  ///
  /// In en, this message translates to:
  /// **'Your watchlist syncs across devices once you sign in.'**
  String get watchlistSheetBody;

  /// No description provided for @watchlistFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed: {detail}'**
  String watchlistFailed(String detail);

  /// No description provided for @loginWelcomeBack.
  ///
  /// In en, this message translates to:
  /// **'Welcome back'**
  String get loginWelcomeBack;

  /// No description provided for @loginCreateAccount.
  ///
  /// In en, this message translates to:
  /// **'Create your account'**
  String get loginCreateAccount;

  /// No description provided for @loginSubtitleSignUp.
  ///
  /// In en, this message translates to:
  /// **'Sign up to save watchlists and unlock premium picks.'**
  String get loginSubtitleSignUp;

  /// No description provided for @loginSubtitleSignIn.
  ///
  /// In en, this message translates to:
  /// **'Sign in to continue your research.'**
  String get loginSubtitleSignIn;

  /// No description provided for @loginEmail.
  ///
  /// In en, this message translates to:
  /// **'Email'**
  String get loginEmail;

  /// No description provided for @loginPassword.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get loginPassword;

  /// No description provided for @loginErrorRequired.
  ///
  /// In en, this message translates to:
  /// **'Required'**
  String get loginErrorRequired;

  /// No description provided for @loginErrorEmail.
  ///
  /// In en, this message translates to:
  /// **'Enter a valid email'**
  String get loginErrorEmail;

  /// No description provided for @loginErrorPasswordShort.
  ///
  /// In en, this message translates to:
  /// **'At least 6 characters'**
  String get loginErrorPasswordShort;

  /// No description provided for @loginConfirmInbox.
  ///
  /// In en, this message translates to:
  /// **'Check your inbox to confirm your email, then sign in.'**
  String get loginConfirmInbox;

  /// No description provided for @loginSignIn.
  ///
  /// In en, this message translates to:
  /// **'Sign in'**
  String get loginSignIn;

  /// No description provided for @loginSignUp.
  ///
  /// In en, this message translates to:
  /// **'Sign up'**
  String get loginSignUp;

  /// No description provided for @loginPromptToSignUp.
  ///
  /// In en, this message translates to:
  /// **'Don\'t have an account? '**
  String get loginPromptToSignUp;

  /// No description provided for @loginPromptToSignIn.
  ///
  /// In en, this message translates to:
  /// **'Already have an account? '**
  String get loginPromptToSignIn;

  /// No description provided for @settingsTitle.
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get settingsTitle;

  /// No description provided for @settingsSectionAccount.
  ///
  /// In en, this message translates to:
  /// **'Account'**
  String get settingsSectionAccount;

  /// No description provided for @settingsSectionSubscription.
  ///
  /// In en, this message translates to:
  /// **'Subscription'**
  String get settingsSectionSubscription;

  /// No description provided for @settingsSectionAbout.
  ///
  /// In en, this message translates to:
  /// **'About'**
  String get settingsSectionAbout;

  /// No description provided for @settingsSectionLanguage.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get settingsSectionLanguage;

  /// No description provided for @settingsSignInCta.
  ///
  /// In en, this message translates to:
  /// **'Sign in or sign up'**
  String get settingsSignInCta;

  /// No description provided for @settingsSignInSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Save your watchlist and unlock premium'**
  String get settingsSignInSubtitle;

  /// No description provided for @settingsSignedInSubtitle.
  ///
  /// In en, this message translates to:
  /// **'User ID: {idShort}…'**
  String settingsSignedInSubtitle(String idShort);

  /// No description provided for @settingsSignOut.
  ///
  /// In en, this message translates to:
  /// **'Sign out'**
  String get settingsSignOut;

  /// No description provided for @settingsPremiumActive.
  ///
  /// In en, this message translates to:
  /// **'Premium active'**
  String get settingsPremiumActive;

  /// No description provided for @settingsPremiumActiveSubtitle.
  ///
  /// In en, this message translates to:
  /// **'You have access to all features'**
  String get settingsPremiumActiveSubtitle;

  /// No description provided for @settingsPremiumUpgrade.
  ///
  /// In en, this message translates to:
  /// **'Upgrade to Premium'**
  String get settingsPremiumUpgrade;

  /// No description provided for @settingsPremiumUpgradeSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Hit rates, splits, full averages'**
  String get settingsPremiumUpgradeSubtitle;

  /// No description provided for @settingsAboutVersion.
  ///
  /// In en, this message translates to:
  /// **'Version {version}'**
  String settingsAboutVersion(String version);

  /// No description provided for @settingsSignOutDialogTitle.
  ///
  /// In en, this message translates to:
  /// **'Sign out?'**
  String get settingsSignOutDialogTitle;

  /// No description provided for @settingsSignOutDialogBody.
  ///
  /// In en, this message translates to:
  /// **'You\'ll need to sign in again to access premium.'**
  String get settingsSignOutDialogBody;

  /// No description provided for @settingsLanguageSystem.
  ///
  /// In en, this message translates to:
  /// **'System default'**
  String get settingsLanguageSystem;

  /// No description provided for @settingsLanguageEnglish.
  ///
  /// In en, this message translates to:
  /// **'English'**
  String get settingsLanguageEnglish;

  /// No description provided for @settingsLanguageTurkish.
  ///
  /// In en, this message translates to:
  /// **'Türkçe'**
  String get settingsLanguageTurkish;

  /// No description provided for @settingsLanguageSpanish.
  ///
  /// In en, this message translates to:
  /// **'Español'**
  String get settingsLanguageSpanish;

  /// No description provided for @settingsLanguagePortuguese.
  ///
  /// In en, this message translates to:
  /// **'Português'**
  String get settingsLanguagePortuguese;

  /// No description provided for @paywallTitle.
  ///
  /// In en, this message translates to:
  /// **'Premium'**
  String get paywallTitle;

  /// No description provided for @paywallHeroTitle.
  ///
  /// In en, this message translates to:
  /// **'Unlock the full edge'**
  String get paywallHeroTitle;

  /// No description provided for @paywallHeroSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Hit rates, splits, and full season averages.'**
  String get paywallHeroSubtitle;

  /// No description provided for @paywallBenefitHitRatesTitle.
  ///
  /// In en, this message translates to:
  /// **'Hit-rate breakdowns'**
  String get paywallBenefitHitRatesTitle;

  /// No description provided for @paywallBenefitHitRatesBody.
  ///
  /// In en, this message translates to:
  /// **'Over/under 2.5, BTTS, AH lines — per team and per league.'**
  String get paywallBenefitHitRatesBody;

  /// No description provided for @paywallBenefitSplitsTitle.
  ///
  /// In en, this message translates to:
  /// **'Home / away splits'**
  String get paywallBenefitSplitsTitle;

  /// No description provided for @paywallBenefitSplitsBody.
  ///
  /// In en, this message translates to:
  /// **'See where teams over- and under-perform vs the market.'**
  String get paywallBenefitSplitsBody;

  /// No description provided for @paywallBenefitRefereeTitle.
  ///
  /// In en, this message translates to:
  /// **'Referee deep-dive'**
  String get paywallBenefitRefereeTitle;

  /// No description provided for @paywallBenefitRefereeBody.
  ///
  /// In en, this message translates to:
  /// **'Cards, penalties, and historical patterns by official.'**
  String get paywallBenefitRefereeBody;

  /// No description provided for @paywallNoPlans.
  ///
  /// In en, this message translates to:
  /// **'No subscription plans are configured yet. Add an offering in the RevenueCat dashboard to enable purchases.'**
  String get paywallNoPlans;

  /// No description provided for @paywallContinue.
  ///
  /// In en, this message translates to:
  /// **'Continue'**
  String get paywallContinue;

  /// No description provided for @paywallRestore.
  ///
  /// In en, this message translates to:
  /// **'Restore purchases'**
  String get paywallRestore;

  /// No description provided for @paywallUnlocked.
  ///
  /// In en, this message translates to:
  /// **'Premium unlocked.'**
  String get paywallUnlocked;

  /// No description provided for @paywallRestored.
  ///
  /// In en, this message translates to:
  /// **'Purchases restored.'**
  String get paywallRestored;

  /// No description provided for @paywallNothingToRestore.
  ///
  /// In en, this message translates to:
  /// **'Nothing to restore.'**
  String get paywallNothingToRestore;

  /// No description provided for @paywallLegal.
  ///
  /// In en, this message translates to:
  /// **'Subscriptions renew automatically until cancelled. Manage in the App Store or Play Store.'**
  String get paywallLegal;

  /// No description provided for @paywallGateLabel.
  ///
  /// In en, this message translates to:
  /// **'Unlock with {tier}'**
  String paywallGateLabel(String tier);

  /// No description provided for @commonCancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get commonCancel;

  /// No description provided for @commonClose.
  ///
  /// In en, this message translates to:
  /// **'Close'**
  String get commonClose;

  /// No description provided for @commonTryAgain.
  ///
  /// In en, this message translates to:
  /// **'Try again'**
  String get commonTryAgain;

  /// No description provided for @commonRetry.
  ///
  /// In en, this message translates to:
  /// **'Try again'**
  String get commonRetry;

  /// No description provided for @commonGenericError.
  ///
  /// In en, this message translates to:
  /// **'Couldn\'t load this'**
  String get commonGenericError;

  /// No description provided for @commonNothingHere.
  ///
  /// In en, this message translates to:
  /// **'Nothing to show yet.'**
  String get commonNothingHere;

  /// No description provided for @commonLive.
  ///
  /// In en, this message translates to:
  /// **'LIVE'**
  String get commonLive;

  /// No description provided for @commonFinalShort.
  ///
  /// In en, this message translates to:
  /// **'FT'**
  String get commonFinalShort;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'es', 'pt', 'tr'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'es':
      return AppLocalizationsEs();
    case 'pt':
      return AppLocalizationsPt();
    case 'tr':
      return AppLocalizationsTr();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
