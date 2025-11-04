import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { User } from '@geonature/components/auth/auth.service';
import { ConfigService } from '@geonature/services/config.service';
import { ModuleService } from '@geonature/services/module.service';
import { Observable } from 'rxjs';
import { FolderData } from '../components/module/interfaces';

@Injectable({
  providedIn: 'root',
})
export class DemarcheSimplifieeService {
  constructor(
    private http: HttpClient,
    private config: ConfigService,
    private module: ModuleService
  ) {}

  getFolder(folderNumber: string): Observable<FolderData> {
    const apiUrl = `${this.config.API_ENDPOINT}/${this.config.PLUGIN_DEPOBIO.MODULE_URL}/get_folder/${folderNumber}`;
    return this.http.get<FolderData>(apiUrl);
  }

  createAFUrl(folderData: FolderData, user: User): string {
    const params = new URLSearchParams({
      id: folderData.id,
      libelle: folderData.libelle,
      description: folderData.description,
      number: String(folderData.number),
      state: folderData.state,
      date_fin: folderData.date_fin,
      user: user.id_role,
      organism: String(user.id_organisme),
    });
    return `${this.config.URL_APPLICATION}/#/${this.module.getModule('METADATA').module_url}/af?${params.toString()}`;
  }
}
