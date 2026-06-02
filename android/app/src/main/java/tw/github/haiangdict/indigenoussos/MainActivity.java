package tw.github.haiangdict.indigenoussos;

import android.content.Intent;
import android.os.Bundle;
import com.getcapacitor.BridgeActivity;
import com.getcapacitor.PluginHandle;
import ee.forgr.capacitor.social.login.SocialLoginPlugin;
import ee.forgr.capacitor.social.login.ModifiedMainActivityForSocialLoginPlugin;
import ee.forgr.capacitor.social.login.GoogleProvider;

public class MainActivity extends BridgeActivity implements ModifiedMainActivityForSocialLoginPlugin {

  @Override
  public void IHaveModifiedTheMainActivityForTheUseWithSocialLoginPlugin() {
    // Required by ModifiedMainActivityForSocialLoginPlugin interface
  }

  @Override
  public void onCreate(Bundle savedInstanceState) {
    registerPlugin(SocialLoginPlugin.class);
    super.onCreate(savedInstanceState);
  }

  @Override
  public void onActivityResult(int requestCode, int resultCode, Intent data) {
    super.onActivityResult(requestCode, resultCode, data);
    if (requestCode >= GoogleProvider.REQUEST_AUTHORIZE_GOOGLE_MIN
        && requestCode < GoogleProvider.REQUEST_AUTHORIZE_GOOGLE_MAX) {
      PluginHandle pluginHandle = getBridge().getPlugin("SocialLogin");
      if (pluginHandle != null) {
        SocialLoginPlugin plugin = (SocialLoginPlugin) pluginHandle.getInstance();
        if (plugin != null) {
          plugin.handleGoogleLoginIntent(requestCode, data);
        }
      }
    }
  }
}