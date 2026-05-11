// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Turkish (`tr`).
class AppLocalizationsTr extends AppLocalizations {
  AppLocalizationsTr([String locale = 'tr']) : super(locale);

  @override
  String get appTitle => 'Shoebox';

  @override
  String get navLeagues => 'Ligler';

  @override
  String get navWatchlist => 'Listem';

  @override
  String get navAccount => 'Hesap';

  @override
  String get sportFootball => 'Futbol';

  @override
  String get sportBasketball => 'Basketbol';

  @override
  String get homePopular => 'Popüler';

  @override
  String get homeAllCompetitions => 'Tüm ligler';

  @override
  String get homeRefereesTooltip => 'Hakemler';

  @override
  String get homeEmpty => 'Bu spor için henüz lig yok.';

  @override
  String get homeOneCompetition => '1 lig';

  @override
  String homeCompetitionsCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count lig',
      one: '1 lig',
      zero: 'Lig yok',
    );
    return '$_temp0';
  }

  @override
  String get watchlistTitle => 'Listem';

  @override
  String get watchlistSignedOutTitle => 'Listeni kullanmak için giriş yap';

  @override
  String get watchlistSignedOutBody =>
      'Maçları kaydet, tüm cihazlarında senkronize tut.';

  @override
  String get watchlistEmpty =>
      'Herhangi bir maçtaki yer işaretine dokun, buraya eklensin.';

  @override
  String get watchlistSheetTitle => 'Maçları kaydetmek için giriş yap';

  @override
  String get watchlistSheetBody =>
      'Listen, giriş yaptıktan sonra cihazlar arasında senkronize olur.';

  @override
  String watchlistFailed(String detail) {
    return 'Başarısız: $detail';
  }

  @override
  String get loginWelcomeBack => 'Tekrar hoş geldin';

  @override
  String get loginCreateAccount => 'Hesap oluştur';

  @override
  String get loginSubtitleSignUp =>
      'Listeni kaydetmek ve premium tahminleri açmak için kaydol.';

  @override
  String get loginSubtitleSignIn => 'Araştırmana devam etmek için giriş yap.';

  @override
  String get loginEmail => 'E-posta';

  @override
  String get loginPassword => 'Şifre';

  @override
  String get loginErrorRequired => 'Zorunlu';

  @override
  String get loginErrorEmail => 'Geçerli bir e-posta gir';

  @override
  String get loginErrorPasswordShort => 'En az 6 karakter';

  @override
  String get loginConfirmInbox =>
      'E-postanı doğrulamak için gelen kutuna bak, sonra giriş yap.';

  @override
  String get loginSignIn => 'Giriş yap';

  @override
  String get loginSignUp => 'Kaydol';

  @override
  String get loginPromptToSignUp => 'Hesabın yok mu? ';

  @override
  String get loginPromptToSignIn => 'Zaten hesabın var mı? ';

  @override
  String get settingsTitle => 'Ayarlar';

  @override
  String get settingsSectionAccount => 'Hesap';

  @override
  String get settingsSectionSubscription => 'Abonelik';

  @override
  String get settingsSectionAbout => 'Hakkında';

  @override
  String get settingsSectionLanguage => 'Dil';

  @override
  String get settingsSignInCta => 'Giriş yap veya kaydol';

  @override
  String get settingsSignInSubtitle => 'Listeni kaydet, premium kilidini aç';

  @override
  String settingsSignedInSubtitle(String idShort) {
    return 'Kullanıcı ID: $idShort…';
  }

  @override
  String get settingsSignOut => 'Çıkış yap';

  @override
  String get settingsPremiumActive => 'Premium aktif';

  @override
  String get settingsPremiumActiveSubtitle => 'Tüm özelliklere erişimin var';

  @override
  String get settingsPremiumUpgrade => 'Premium\'a yükselt';

  @override
  String get settingsPremiumUpgradeSubtitle =>
      'Hit oranları, ev/deplasman, tüm ortalamalar';

  @override
  String settingsAboutVersion(String version) {
    return 'Sürüm $version';
  }

  @override
  String get settingsSignOutDialogTitle => 'Çıkış yapılsın mı?';

  @override
  String get settingsSignOutDialogBody =>
      'Premium\'a erişmek için yeniden giriş yapman gerekecek.';

  @override
  String get settingsLanguageSystem => 'Sistem varsayılanı';

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
  String get paywallHeroTitle => 'Tam avantajı aç';

  @override
  String get paywallHeroSubtitle =>
      'Hit oranları, ev/deplasman, tüm sezon ortalamaları.';

  @override
  String get paywallBenefitHitRatesTitle => 'Hit oranı dağılımları';

  @override
  String get paywallBenefitHitRatesBody =>
      'Üst/Alt 2.5, KG Var/Yok, AH bahisleri — takım ve lig bazında.';

  @override
  String get paywallBenefitSplitsTitle => 'Ev / Deplasman';

  @override
  String get paywallBenefitSplitsBody =>
      'Takımlar piyasaya kıyasla nerede over/under performans gösteriyor.';

  @override
  String get paywallBenefitRefereeTitle => 'Hakem analizi';

  @override
  String get paywallBenefitRefereeBody =>
      'Kart, penaltı ve hakeme göre tarihsel örüntüler.';

  @override
  String get paywallNoPlans =>
      'Henüz abonelik planı tanımlanmadı. Satın almayı etkinleştirmek için RevenueCat panelinden offering ekle.';

  @override
  String get paywallContinue => 'Devam et';

  @override
  String get paywallRestore => 'Satın alımları geri yükle';

  @override
  String get paywallUnlocked => 'Premium açıldı.';

  @override
  String get paywallRestored => 'Satın alımlar geri yüklendi.';

  @override
  String get paywallNothingToRestore => 'Geri yüklenecek bir şey yok.';

  @override
  String get paywallLegal =>
      'Abonelikler iptal edilene dek otomatik yenilenir. App Store veya Play Store\'dan yönet.';

  @override
  String paywallGateLabel(String tier) {
    return '$tier ile aç';
  }

  @override
  String get commonCancel => 'İptal';

  @override
  String get commonClose => 'Kapat';

  @override
  String get commonTryAgain => 'Tekrar dene';

  @override
  String get commonRetry => 'Tekrar dene';

  @override
  String get commonGenericError => 'Bu yüklenemedi';

  @override
  String get commonNothingHere => 'Henüz görüntülenecek bir şey yok.';

  @override
  String get commonLive => 'CANLI';

  @override
  String get commonFinalShort => 'MS';
}
