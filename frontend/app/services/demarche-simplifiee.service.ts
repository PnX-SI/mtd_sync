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
      acquisition_framework_name: folderData.libelle,
      acquisition_framework_desc: folderData.description,
      folder_id: String(folderData.number),
      state: folderData.state,
      acquisition_framework_end_date: folderData.date_fin,
      id_role: user.id_role,
      id_organism: String(user.id_organisme),
    });
    return `${this.config.URL_APPLICATION}/#/${this.module.getModule('METADATA').module_url}/af?${params.toString()}`;
  }
}
